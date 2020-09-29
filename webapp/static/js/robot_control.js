//Button
$(document).ready(function() {
  $("#runningButton").change(function() {
    // Send info to flask
    $.getJSON('/robot/set_running', {
      checked: $(this).prop('checked')
    }, function(data) {
      $('#runningButton').prop('checked');
    });
  });
});

//SpeedSlider
function setStates() {
  var min = parseFloat($('#speed')[0].min);
  var max = parseFloat($('#speed')[0].max);
  var step = parseFloat($('#speed')[0].step);

  // Define the ranges for each state
  var low_lower = min + step;
  var low_upper = Math.round((min + 0.4 * (max - min)) * 100) / 100;
  var low = _.range(low_lower, low_upper, step);
  var len_low = low.length
  for (var y = 0; y < len_low; y++) {
    low[y] = Math.round(low[y] * 1e2) / 1e2;
  }

  var med_lower = Math.round((min + 0.4 * (max - min)) * 100) / 100;
  var med_upper = Math.round((min + 0.69 * (max - min)) * 100) / 100;
  var medium = _.range(med_lower, med_upper, step);
  var len_med = medium.length
  for (var y = 0; y < len_med; y++) {
    medium[y] = Math.round(medium[y] * 1e2) / 1e2;
  }

  var high_lower = Math.round((min + 0.7 * (max - min)) * 100) / 100;
  var high_upper = max - step;
  var high = _.range(high_lower, high_upper, step);
  var len_high = high.length
  for (var y = 0; y < len_high; y++) {
    high[y] = Math.round(high[y] * 1e2) / 1e2;
  }

  // Create dict of states
  const sliderStates = [{
      name: "min",
      range: [min]
    },
    {
      name: "low",
      range: low
    },
    {
      name: "med",
      range: medium
    },
    {
      name: "high",
      range: high
    },
    {
      name: "max",
      range: [max]
    },
  ];
  return sliderStates;
}

var currentState;
var handle;
var sliderStates;

// Create speedslider
$(document).ready(function() {
  $('#speed')
    .rangeslider({
      polyfill: false,
      onInit: function() {
        sliderStates = setStates();
        handle = $('.rangeslider__handle', this.range);
        // Load values from storage
        if (localStorage.getItem("speed")
            && this.min < localStorage.getItem("speed")
            && localStorage.getItem("speed") < this.max) {
          this.value = localStorage.getItem("speed")
          $('#speed')[0].value = localStorage.getItem("speed")
        }
        updateHandle(handle[0], this.value);
        updateState(handle[0], this.value);
      }
    })
    .rangeslider('update', true)
    .on('input', function() {
      updateHandle(handle[0], this.value);
      checkState(handle[0], this.value);
      // Store state
      localStorage.setItem("speed", this.value);
      // Send info to flask
      $.getJSON('/robot/change_speed', {
        speed: $(this).prop('value')
      });
    });
});

// Update the value inside the slider handle
function updateHandle(el, val) {
  el.textContent = val;
}

// Check if the slider state has changed
function checkState(el, val) {
  // if the value does not fall in the range of the current state, update that shit.
  if (!_.contains(currentState.range, parseFloat(val))) {
    updateState(el, val);
  }
}

// Change the state of the slider
function updateState(el, val) {
  for (var j = 0; j < sliderStates.length; j++) {
    if (_.contains(sliderStates[j].range, parseFloat(val))) {
      currentState = sliderStates[j];
    }
  }
  // If the state is high, update the handle count to read MAX
  if (currentState.name == "min") {
    updateHandle(handle[0], "MIN");
  }
  // If the state is high, update the handle count to read MAX
  if (currentState.name == "max") {
    updateHandle(handle[0], "MAX");
  }
  // Update handle color
  handle
    .removeClass(function(index, css) {
      return (css.match(/(^|\s)js-\S+/g) || []).join(' ');
    })
    .addClass("js-" + currentState.name);
}

// Function to clear local storage
function clearLocalStorage() {
  localStorage.clear();
}
