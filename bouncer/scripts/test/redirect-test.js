'use strict';

var redirect = require('../redirect.js');

describe('#redirect', function () {
  var settings;
  beforeEach(function () {
    window.chrome = undefined;
    settings = {
      chromeExtensionId: 'test-extension-id',
      extensionUrl: 'http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q',
      viaUrl: 'https://via.hypothes.is/http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q',
    };
    sinon.stub(window.console, 'error');
  });

  afterEach(function () {
    window.console.error.restore();
  });

  it('reads settings from the page by default', function () {
    var settings = {
      chromeExtensionId: 'a-b-c',
      extensionUrl: 'https://example.org/#annotations:123',
      viaUrl: 'https://proxy.it/#annotations:123',
    };
    var settingsEl = document.createElement('script');
    settingsEl.type = 'application/json';
    settingsEl.className = 'js-bouncer-settings';
    settingsEl.textContent = JSON.stringify(settings);
    document.body.appendChild(settingsEl);
    var navigateTo = sinon.stub();

    redirect(navigateTo);

    assert.isTrue(navigateTo.calledWith(settings.viaUrl));
  });

  it('redirects to Via if not Chrome', function () {
    window.chrome = undefined;  // The user isn't using Chrome.
    var navigateTo = sinon.stub();

    redirect(navigateTo, settings);

    assert.equal(navigateTo.calledOnce, true);
    assert.equal(
      navigateTo.calledWithExactly('https://via.hypothes.is/http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q'),
      true);
  });

  it('redirects to Via if window.chrome but no chrome.runtime', function () {
    // Some browsers define window.chrome but not chrome.runtime.
    window.chrome = {};
    var navigateTo = sinon.stub();

    redirect(navigateTo, settings);

    assert.equal(navigateTo.calledOnce, true);
    assert.equal(
      navigateTo.calledWithExactly('https://via.hypothes.is/http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q'),
      true);
  });

  it('redirects to Via if window.chrome but no sendMessage', function () {
    // Some browsers might window.chrome but not chrome.runtime.sendMessage.
    window.chrome = {runtime: {}};
    var navigateTo = sinon.stub();

    redirect(navigateTo, settings);

    assert.equal(navigateTo.calledOnce, true);
    assert.equal(
      navigateTo.calledWithExactly('https://via.hypothes.is/http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q'),
      true);
  });

  it('redirects to Via if Chrome but no extension', function () {
    window.chrome = {
      runtime: {
        sendMessage: function (id, message, callbackFunction) {
          callbackFunction(null);
        },
      },
    };
    var navigateTo = sinon.stub();

    redirect(navigateTo, settings);

    assert.equal(navigateTo.calledOnce, true);
    assert.equal(
      navigateTo.calledWithExactly('https://via.hypothes.is/http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q'),
      true);
  });

  it('redirects to Via if lastError is defined', function () {
    window.chrome = {
      runtime: {
        sendMessage: function (id, message, callbackFunction) {
          callbackFunction('Hey!');
        },
        lastError: {message: 'There was an error'},
      },
    };
    var navigateTo = sinon.stub();

    redirect(navigateTo, settings);

    assert.equal(navigateTo.calledOnce, true);
    assert.equal(
      navigateTo.calledWithExactly('https://via.hypothes.is/http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q'),
      true);
  });

  it('logs an error if lastError is defined', function () {
    window.chrome = {
      runtime: {
        sendMessage: function (id, message, callbackFunction) {
          callbackFunction('Hey!');
        },
        lastError: {message: 'There was an error'},
      },
    };

    redirect(sinon.stub(), settings);

    assert.equal(console.error.called, true);
  });

  it('calls chrome.runtime.sendMessage correctly', function () {
    window.chrome = {
      runtime: {
        sendMessage: sinon.stub(),
      },
    };

    redirect(function () {}, settings);

    assert.equal(window.chrome.runtime.sendMessage.calledOnce, true);
    assert.equal(window.chrome.runtime.sendMessage.firstCall.args[0],
      'test-extension-id');
    assert.deepEqual(window.chrome.runtime.sendMessage.firstCall.args[1],
      {type: 'ping'});
    assert.equal(typeof(window.chrome.runtime.sendMessage.firstCall.args[2]),
      'function');
  });

  it('redirects to Chrome extension if installed', function () {
    window.chrome = {
      runtime: {
        sendMessage: function (id, message, callbackFunction) {
          callbackFunction('Hey!');
        },
      },
    };
    var navigateTo = sinon.stub();

    redirect(navigateTo, settings);

    assert.equal(navigateTo.calledOnce, true);
    assert.equal(
      navigateTo.calledWithExactly('http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q'),
      true);
  });

  it('redirects to original URL if no Via URL provided', function () {
    settings.viaUrl = null;
    var navigateTo = sinon.stub();

    redirect(navigateTo, settings);

    assert.isTrue(navigateTo.calledOnce);
    assert.isTrue(navigateTo.calledWithExactly(settings.extensionUrl));
  });
});
