'use strict';

var nodeFirefox = require('node-firefox');

nodeFirefox.startSimulator().then(function(simulator) {
  nodeFirefox.connect(simulator.port).then(function(client) {
    console.log(client);
  });
});
