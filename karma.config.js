module.exports = function (config) {
  config.set({
    basePath: '',
    frameworks: ['chai', 'mocha', 'sinon'],
    files: [
      { pattern: 'bouncer/scripts/*.js', type: 'module', included: false },
      { pattern: 'bouncer/**/*-test.js', type: 'module' },
    ],
    reporters: ['progress'],
    port: 9876,
    colors: true,
    logLevel: config.LOG_INFO,
    autoWatch: false,
    browsers: ['ChromeHeadless'],
    singleRun: true,
    concurrency: Infinity
  });
};
