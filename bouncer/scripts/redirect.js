'use strict';

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
    document.querySelector('script.js-bouncer-settings').textContent);
}

/** Navigate the browser to the given URL. */
function defaultNavigateTo(url) {
  window.location.replace(url);
}

/**
 * Navigate the browser to the requested annotation.
 *
 * If the browser is Chrome and our Chrome extension is installed then
 * navigate to the annotation's direct link for the Chrome extension.
 * If the Chrome extension isn't installed or the browser isn't Chrome then
 * navigate to the annotation's Via direct link.
 *
 * @param {(url: string) => void} [navigateTo]
 * @param {Settings} [settings]
 */
function redirect(navigateTo, settings) {
  navigateTo = navigateTo || defaultNavigateTo; // Test seam
  settings = settings || getSettings(document); // Test seam

  // If the proxy cannot be used with this URL, send the user directly to the
  // original page.
  if (!settings.viaUrl) {
    navigateTo(settings.extensionUrl);
    return;
  }

  var chrome = window.chrome;
  if (chrome && chrome.runtime && chrome.runtime.sendMessage) {
    // The user is using Chrome, redirect them to our Chrome extension if they
    // have it installed, via otherwise.
    chrome.runtime.sendMessage(
      settings.chromeExtensionId,
      {type: 'ping'},
      function (response) {
        var url;

        if (response && !chrome.runtime.lastError) {
          // The user has our Chrome extension installed :)
          url = settings.extensionUrl;
        } else {
          if (chrome.runtime.lastError) {
            console.error(chrome.runtime.lastError);
          }
          // The user doesn't have our Chrome extension installed :(
          url = settings.viaUrl;
        }

        navigateTo(url);
      }
    );
  } else {
    // The user isn't using Chrome, just redirect them to Via.
    navigateTo(settings.viaUrl);
  }
}

if (typeof module === 'object') {
  // Browserify is present, this file must be being run by the tests.
  module.exports = redirect;
} else {
  // Browserify is not present, this file must be being run in development or
  // production.
  redirect();
}
