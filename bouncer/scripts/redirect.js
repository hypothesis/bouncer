/**
 * Configuration information for the client-side code that detects the best way
 * to route the user to a URL with Hypothesis activated and specified
 * annotations selected.
 *
 * This is rendered into Bouncer's interstitial page by the backend service.
 *
 * @typedef {Object} Settings
 * @prop {string} chromeExtensionId - ID of the Chrome extension that Bouncer
 *   should check for in the user's browser.
 * @prop {string} extensionUrl - Original URL of the page plus a fragment that
 *   triggers the extension to activate when the user visits the page. This is
 *   also used in cases where the original URL embeds the client.
 * @prop {string|null} viaUrl - Proxy URL of `null` if the proxy cannot be used
 *   to display this annotation in context.
 */

/**
 * Return the settings object that the server injected into the page.
 *
 * @return {Settings}
 */
function getSettings(document) {
  return JSON.parse(
    document.querySelector('script.js-bouncer-settings').textContent
  );
}

/** Navigate the browser to the given URL. */
function defaultNavigateTo(url) {
  window.location.replace(url);
}

/**
 * Wrapper around `chrome.runtime.sendMessage` [1] which returns a Promise.
 *
 * [1] https://developer.chrome.com/docs/extensions/mv3/messaging/#external-webpage
 *
 * @param {string} extensionId
 * @param {object} data
 * @return {Promise} Promise that resolves with the result of the call returned
 *   by the extension or rejects if an error was reported via `chrome.runtime.lastError`.
 */
function sendMessage(extensionId, data) {
  const chrome = window.chrome;
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(extensionId, data, result => {
      if (chrome.runtime.lastError) {
        reject(chrome.runtime.lastError);
      } else {
        resolve(result);
      }
    });
  });
}

/**
 * Navigate the browser to the requested annotation.
 *
 * If the browser is Chrome and our Chrome extension is installed then
 * navigate to the annotation's direct link for the Chrome extension.
 * If the Chrome extension isn't installed or the browser isn't Chrome then
 * navigate to the annotation's Via direct link.
 *
 * Returns a Promise which resolves after the navigation to the annotation's
 * URL has been initiated.
 *
 * @param {(url: string) => void} [navigateTo] - Test seam. Function that
 *   performs a navigation by modifying `location.href`.
 * @param {Settings} [settings] - Test seam. Configuration for the extension
 *   and redirect.
 */
export async function redirect(
  navigateTo = defaultNavigateTo,
  settings = getSettings(document)
) {
  // If the proxy cannot be used with this URL, send the user directly to the
  // original page.
  if (!settings.viaUrl) {
    navigateTo(settings.extensionUrl);
    return;
  }

  if (settings.alwaysUseVia) {
    navigateTo(settings.viaUrl);
    return;
  }

  const chrome = window.chrome;
  if (chrome && chrome.runtime && chrome.runtime.sendMessage) {
    // The user is using Chrome, redirect them to our Chrome extension if they
    // have it installed, via otherwise.
    try {
      const response = await sendMessage(settings.chromeExtensionId, {
        type: 'ping',
        queryFeatures: ['activate'],
      });
      // The user has our Chrome extension installed :)
      if (response.features && response.features.includes('activate')) {
        // Extension supports "activate" API that will let it handle
        // redirection and activation.
        const parsedURL = new URL(settings.extensionUrl);
        const query = parsedURL.hash;
        parsedURL.hash = '';
        const urlWithoutFragment = parsedURL.toString();

        try {
          await sendMessage(settings.chromeExtensionId, {
            type: 'activate',
            url: urlWithoutFragment,
            query,
          });
        } catch (err) {
          console.error('Failed to activate extension', err);
        }
      } else {
        // For older extensions, fall back to a normal client-side redirect.
        // The installed extension(s) will notice the URL fragment and
        // activate. The downside is that if the user has multiple builds
        // of the Hypothesis extension installed, it is unpredictable as
        // to which will activate first and "win" the race to inject.
        navigateTo(settings.extensionUrl);
      }
    } catch (err) {
      // The user doesn't have our Chrome extension installed, or we couldn't
      // connect to it.
      console.error(err);
      navigateTo(settings.viaUrl);
    }
  } else {
    // The user isn't using Chrome, just redirect them to Via.
    navigateTo(settings.viaUrl);
  }
}

if (!('__karma__' in window)) {
  // Check if in test environment
  redirect();
}
