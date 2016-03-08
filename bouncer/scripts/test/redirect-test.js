'use strict';

var redirect = require('../redirect.js');

describe('redirect()', function () {
  beforeEach(function () {
    window.chrome = undefined;
    window.document.querySelector = function () {
      return {
        textContent: JSON.stringify({
          extensionUrl: 'http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q',
          viaUrl: 'https://via.hypothes.is/http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q',
        })
      };
    };
    sinon.stub(window.console, 'error');
  });

  afterEach(function () {
    window.console.error.restore();
  });

  it('redirects to Via if not Chrome', function () {
    window.chrome = undefined;  // The user isn't using Chrome.
    var navigateTo = sinon.stub();

    redirect(navigateTo);

    assert.equal(navigateTo.calledOnce, true);
    assert.equal(
      navigateTo.calledWithExactly('https://via.hypothes.is/http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q'),
      true);
  });

  it('redirects to Via if window.chrome but no chrome.runtime', function () {
    // Some browsers define window.chrome but not chrome.runtime.
    window.chrome = {}
    var navigateTo = sinon.stub();

    redirect(navigateTo);

    assert.equal(navigateTo.calledOnce, true);
    assert.equal(
      navigateTo.calledWithExactly('https://via.hypothes.is/http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q'),
      true);
  });

  it('redirects to Via if window.chrome but no sendMessage', function () {
    // Some browsers might window.chrome but not chrome.runtime.sendMessage.
    window.chrome = {runtime: {}}
    var navigateTo = sinon.stub();

    redirect(navigateTo);

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
        }
      }
    };
    var navigateTo = sinon.stub();

    redirect(navigateTo);

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
        lastError: {message: 'There was an error'}
      }
    };
    var navigateTo = sinon.stub();

    redirect(navigateTo);

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
        lastError: {message: 'There was an error'}
      }
    };

    redirect(sinon.stub());

    assert.equal(console.error.called, true);
  });

  it('redirects to Chrome extension if installed', function () {
    window.chrome = {
      runtime: {
        sendMessage: function (id, message, callbackFunction) {
          callbackFunction('Hey!');
        }
      }
    };
    var navigateTo = sinon.stub();

    redirect(navigateTo);

    assert.equal(navigateTo.calledOnce, true);
    assert.equal(
      navigateTo.calledWithExactly('http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q'),
      true);
  });
});
