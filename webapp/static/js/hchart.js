var chart_io;
var chart_pid;
var chart_bat;
var chart_speed;
/**
 * Inspiration from:
 * https://github.com/tdiethe/flask-live-charts
 * Request data from the server, add it to the graph and set a timeout
 * to request again
 * NOTe: could be done with single update. This was easier to implement tho!
 */
function requestDataCtrl() {
    $.ajax({
        url: '/robot/chart_stream',
        data: { 'iwantthis': 'CTRL'},
        datatype: 'json',
        success: function(new_points) {
            for (const [idx, point] of new_points.entries()) {
                var series = chart_io.series[idx],
                    shift = series.data.length > 20; // shift if the series is
                                                    // longer than 20
                // add the point
                chart_io.series[idx].addPoint(point, true, shift);
            }
            // call it again after one second
            setTimeout(requestDataCtrl, 1000);
        },
        error: function() {
            console.log('https://www.youtube.com/watch?v=R3uqvoKZano')
        },
        cache: false
    });
}

function requestDataPID() {
    $.ajax({
        url: '/robot/chart_stream',
        data: { 'iwantthis': 'PID'},
        datatype: 'json',
        success: function(new_points) {
            for (const [idx, point] of new_points.entries()) {
                //var series = chart_pid.series[idx],
                var shift = chart_pid.series[idx].data.length > 20; // shift if the series is
                                                    // longer than 20
                // add the point
                chart_pid.series[idx].addPoint(point, true, shift);
            }
            // call it again after one second
            setTimeout(requestDataPID, 1000);
        },
        error: function() {
            console.log('https://www.youtube.com/watch?v=R3uqvoKZano')
        },
        cache: false
    });
}

function requestDataSpeed() {
    $.ajax({
        url: '/robot/chart_stream',
        data: { 'iwantthis': 'SPEED'},
        datatype: 'json',
        success: function(new_points) {
            for (const [idx, point] of new_points.entries()) {
                //var series = chart_pid.series[idx],
                var shift = chart_speed.series[idx].data.length > 20; // shift if the series is
                                                    // longer than 20
                // add the point
                chart_speed.series[idx].addPoint(point, true, shift);
            }
            // call it again after one second
            setTimeout(requestDataSpeed, 1000);
        },
        error: function() {
            console.log('https://www.youtube.com/watch?v=R3uqvoKZano')
        },
        cache: false
    });
}

function requestDataBattery() {
    $.ajax({
        url: '/robot/battery_level',
        data: { 'with_datestamp': true },
        datatype: 'json',
        success: function(point) {
            var shift = chart_bat.series[0].data.length > 20; // shift if the series is
                                                             // longer than 20
            // add the point
            chart_bat.series[0].addPoint(point, true, shift);
            // call it again after one second
            setTimeout(requestDataBattery, 30000);
        },
        error: function() {
            console.log('https://www.youtube.com/watch?v=R3uqvoKZano')
        },
        cache: false
    });
}

$(document).ready(function() {
    // Input & Output
    chart_io = new Highcharts.Chart({
        chart: {
            renderTo: 'data-container-CONTROL',
            defaultSeriesType: 'line',
            events: {
                load: requestDataCtrl
            }
        },
        title: {
            text: 'Input output'
        },
        //xAxis: {
        //    //tickPixelInterval: 150,
        //    maxZoom: 20 * 1000
        //},
        yAxis: {
            minPadding: 0.2,
            maxPadding: 0.2,
            title: {
                text: 'Value',
                margin: 5
            }
        },
        series: [
            {
                name: 'Offset 1',
                data: []
            },
            {
                name: 'Offset 2',
                data: []
            },
            {
                name: 'Steering',
                data: []
            },


        ]
    });

    // Battery values:
    chart_pid = new Highcharts.Chart({
        chart: {
            renderTo: 'data-container-PID',
            defaultSeriesType: 'line',
            events: {
                load: requestDataPID
            }
        },
        title: {
            text: 'PID values'
        },
        //xAxis: {
        //    //tickPixelInterval: 150,
        //    maxZoom: 20 * 1000
        //},
        yAxis: {
            minPadding: 0.2,
            maxPadding: 0.2

        },
        series: [
            {
                name: 'P',
                data: []
            },
            {
                name: 'I',
                data: []
            },
            {
                name: 'D',
                data: []
            },
            {
                name: 'dP',
                data: []
            },
            {
                name: 'dI',
                data: []
            },
            {
                name: 'dD',
                data: []
            },

        ]
    });

    chart_bat = new Highcharts.Chart({
        chart: {
            renderTo: 'data-container-BATTERY',
            defaultSeriesType: 'spline',
            events: {
                load: requestDataBattery
            }
        },
        title: {
            text: 'Battery level'
        },
        //xAxis: {
        //    //tickPixelInterval: 150,
        //    maxZoom: 20 * 1000
        //},
        yAxis: {
            minPadding: 0.2,
            maxPadding: 0.2
        },
        series: [
            {
                name: 'Battery level (V)',
                data: []
            }
        ]
    });

    // Battery values:
    chart_pid = new Highcharts.Chart({
        chart: {
            renderTo: 'data-container-PID',
            defaultSeriesType: 'line',
            events: {
                load: requestDataPID
            }
        },
        title: {
            text: 'PID values'
        },
        //xAxis: {
        //    //tickPixelInterval: 150,
        //    maxZoom: 20 * 1000
        //},
        yAxis: {
            minPadding: 0.2,
            maxPadding: 0.2

        },
        series: [
            {
                name: 'P',
                data: []
            },
            {
                name: 'I',
                data: []
            },
            {
                name: 'D',
                data: []
            },
            {
                name: 'dP',
                data: []
            },
            {
                name: 'dI',
                data: []
            },
            {
                name: 'dD',
                data: []
            },

        ]
    });

    chart_speed = new Highcharts.Chart({
        chart: {
            renderTo: 'data-container-SPEED',
            defaultSeriesType: 'spline',
            events: {
                load: requestDataSpeed
            }
        },
        title: {
            text: 'Robot speed'
        },
        //xAxis: {
        //    //tickPixelInterval: 150,
        //    maxZoom: 20 * 1000
        //},
        yAxis: {
            minPadding: 0.2,
            maxPadding: 0.2
        },
        series: [
            {
                name: 'Speed',
                data: []
            }
        ]
    });

});
