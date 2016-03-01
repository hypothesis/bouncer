'use strict';

/** The ID of the Chrome extension we want to talk to. */
var EDITOR_EXTENSION_ID = 'oldbkmekfdjiffgkconlamcngmkioffd';

/** Return the settings object that the server injected into the page. */
function getSettings(document) {
  return JSON.parse(
    document.querySelector('script.js-bouncer-settings').textContent);
}

var SETTINGS = getSettings(document);

/** Configure Raven to report any crashes to Sentry. */
Raven.config(
    SETTINGS.sentry_javascript_dsn,
    {'release': SETTINGS.version}
  ).install();


/** Navigate the browser to the given URL. */
function navigateTo(url) {
  window.location = url;
}

/** Navigate the browser to the requested annotation.
 *
 * If the browser is Chrome and our Chrome extension is installed then
 * navigate to the annotation's direct link for the Chrome extension.
 * If the Chrome extension isn't installed or the browser isn't Chrome then
 * navigate to the annotation's Via direct link.
 *
 */
function redirect(navigateToFn) {
  // Use the test navigateTo() function if one was passed in, the real
  // navigateTo() otherwise.
  navigateTo = navigateToFn || navigateTo;

  if (window.chrome && chrome.runtime && chrome.runtime.sendMessage) {
    // The user is using Chrome, redirect them to our Chrome extension if they
    // have it installed, via otherwise.
    chrome.runtime.sendMessage(
      EDITOR_EXTENSION_ID,
      {type: 'ping'},
      function (response) {
        var url;
        if (response) {
          // The user has our Chrome extension installed :)
          url = SETTINGS.extensionUrl;
        } else {
          // The user doesn't have our Chrome extension installed :(
          url = SETTINGS.viaUrl;
        }
        navigateTo(url);
      }
    );
  } else {
    // The user isn't using Chrome, just redirect them to Via.
    navigateTo(SETTINGS.viaUrl);
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
