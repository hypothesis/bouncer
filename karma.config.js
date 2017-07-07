module.exports = function (config) {
  config.set({
    browserify: {
      debug: true
    },
    basePath: '',
    frameworks: ['browserify', 'chai', 'mocha', 'sinon'],
    files: [
      'bouncer/**/*-test.js'
    ],
    preprocessors: {
      '**/*-test.js': ['browserify']
    },
    reporters: ['progress'],
    port: 9876,
    colors: true,
    logLevel: config.LOG_INFO,
    autoWatch: false,
    browsers: ['PhantomJS'],
    singleRun: true,
    concurrency: Infinity
  });
};
