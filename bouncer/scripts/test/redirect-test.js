import { redirect } from '../redirect.js';

describe('#redirect', () => {
  /**
   * Error message which a `chrome.runtime.sendMessage` request fails with
   * if the extension does not exist. This is reported via `chrome.runtime.lastError`
   * inside the `sendMessage` callback.
   */
  const extensionConnectError = {
    message: 'Could not establish connection. Receiving end does not exist.',
  };

  let settings;
  beforeEach(() => {
    window.chrome = undefined;
    settings = {
      chromeExtensionId: 'test-extension-id',
      extensionUrl:
        'http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q',
      viaUrl:
        'https://via.hypothes.is/http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q',
    };
    sinon.stub(window.console, 'error');
  });

  afterEach(() => {
    window.console.error.restore();
  });

  it('reads settings from the page', () => {
    const settings = {
      chromeExtensionId: 'a-b-c',
      extensionUrl: 'https://example.org/#annotations:123',
      viaUrl: 'https://proxy.it/#annotations:123',
    };
    const settingsEl = document.createElement('script');
    settingsEl.type = 'application/json';
    settingsEl.className = 'js-bouncer-settings';
    settingsEl.textContent = JSON.stringify(settings);
    document.body.appendChild(settingsEl);
    const navigateTo = sinon.stub();

    redirect(navigateTo);

    assert.isTrue(navigateTo.calledWith(settings.viaUrl));
  });

  [
    // Browser is not Chrome
    undefined,

    // `chrome` global exists, but `runtime` property missing
    {},

    // `chrome.runtime` exists, but `sendMessage` function is missing
    { runtime: {} },
  ].forEach(chrome => {
    it('redirects to Via if `chrome.runtime.sendMessage` API not available', () => {
      // Some browsers define window.chrome but not chrome.runtime.
      window.chrome = chrome;
      const navigateTo = sinon.stub();

      redirect(navigateTo, settings);

      assert.equal(navigateTo.calledOnce, true);
      assert.equal(
        navigateTo.calledWithExactly(
          'https://via.hypothes.is/http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q'
        ),
        true
      );
    });
  });

  it('sends "ping" request to extension', () => {
    window.chrome = {
      runtime: {
        sendMessage: sinon.stub(),
      },
    };

    redirect(() => {}, settings);

    sinon.assert.calledWith(
      window.chrome.runtime.sendMessage,
      'test-extension-id',
      {
        type: 'ping',
        queryFeatures: ['activate'],
      },
      sinon.match.func
    );
  });

  it('redirects to Via if "ping" request to extension fails', async () => {
    window.chrome = {
      runtime: {
        sendMessage: (id, message, callbackFunction) => {
          callbackFunction();
        },
        lastError: extensionConnectError,
      },
    };
    const navigateTo = sinon.stub();

    await redirect(navigateTo, settings);

    sinon.assert.calledWith(console.error, window.chrome.runtime.lastError);
    assert.equal(navigateTo.calledOnce, true);
    assert.equal(
      navigateTo.calledWithExactly(
        'https://via.hypothes.is/http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q'
      ),
      true
    );
  });

  it('redirects to extension if "ping" request succeeds and "activate" is not supported', async () => {
    window.chrome = {
      runtime: {
        sendMessage: (id, message, callbackFunction) => {
          callbackFunction({ type: 'pong' });
        },
      },
    };
    const navigateTo = sinon.stub();

    await redirect(navigateTo, settings);

    assert.equal(navigateTo.calledOnce, true);
    assert.equal(
      navigateTo.calledWithExactly(
        'http://www.example.com/example.html#annotations:AVLlVTs1f9G3pW-EYc6q'
      ),
      true
    );
  });

  it('navigates to annotation URL using "activate" message to extension', async () => {
    window.chrome = {
      runtime: {
        sendMessage: sinon.spy((id, message, callbackFunction) => {
          callbackFunction({ type: 'pong', features: ['activate'] });
        }),
      },
    };
    const navigateTo = sinon.stub();

    await redirect(navigateTo, settings);

    sinon.assert.calledWith(
      window.chrome.runtime.sendMessage,
      'test-extension-id',
      {
        type: 'activate',
        url: settings.extensionUrl.replace(/#.*$/, ''),
        query: new URL(settings.extensionUrl).hash,
      },
      sinon.match.func
    );
  });

  it('redirects to original URL if no Via URL provided', () => {
    settings.viaUrl = null;
    const navigateTo = sinon.stub();

    redirect(navigateTo, settings);

    assert.isTrue(navigateTo.calledOnce);
    assert.isTrue(navigateTo.calledWithExactly(settings.extensionUrl));
  });

  it('redirects to Via if `alwaysUseVia` is true', () => {
    settings.alwaysUseVia = true;
    const navigateTo = sinon.stub();

    redirect(navigateTo, settings);

    assert.isTrue(navigateTo.calledOnce);
    assert.isTrue(navigateTo.calledWithExactly(settings.viaUrl));
  });
});
