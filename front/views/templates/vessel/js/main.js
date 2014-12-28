var chosen_marker_obj = null;

function view(map, lat, lon, zoom) {
    if (zoom == undefined) zoom = 5;
    map.setView([lat, lon], zoom);

    L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
        minZoom: 2,
        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

    map.on('popupclose', function(e) {
        if (chosen_marker_obj) {
            var icon_url = chosen_marker_obj.attr('src').replace('chosen-marker.png', 'marker.png');
            chosen_marker_obj.attr('src', icon_url);
            chosen_marker_obj = null;
        }
    })
}

function mark(map, lat, lon, heading, popup) {
    var marker = L.marker([lat, lon],
                          {icon: getIcon(heading)}).addTo(map);
    var marker_obj = $(".leaflet-marker-icon").last()[0];
    var _trans_val = jQuery.style(marker_obj, 'transform');
    jQuery.style(marker_obj, 'transform', _trans_val + ' rotate(' + heading + 'deg)')

    marker.bindPopup(popup);
    marker.on('click', function(e) {
        marker.openPopup();
        chosen_marker_obj = $(marker_obj);
        var icon_url = chosen_marker_obj.attr('src').replace('marker.png', 'chosen-marker.png');
        chosen_marker_obj.attr('src', icon_url);
    });
    marker.on('mouseover', function(e) {
        if (chosen_marker_obj) return;
        marker.openPopup();
    });
    marker.on('mouseout', function(e) {
        if (chosen_marker_obj) return;
        marker.closePopup();
    });
}

function getIcon(degree) {
    return L.icon({
        iconUrl: '/templates/vessel/img/marker.png',
        iconSize: [25, 25],
        iconAnchor: [12, 0],
    });
}

function refresh_countdown(obj, interval) {
    var t_secs = parseInt(obj.attr('total_seconds'));
    t_secs = t_secs - interval;
    if (t_secs < 0) t_secs = 0;
    obj.attr('total_seconds', t_secs);
    var days = parseInt(t_secs/(24 * 3600));
    var hours = parseInt((t_secs - 24 * 3600 * days) / 3600);
    var mins = parseInt((t_secs - 24 * 3600 * days) % 3600 / 60);
    obj.find('.day-num').text(days);
    obj.find('.hour-num').text(hours);
    obj.find('.minute-num').text(mins);
    if (days > 0)
        obj.find('.day').show();
    else
        obj.find('.day').hide();
    if (hours > 0)
        obj.find('.hour').show();
    else
        obj.find('.hour').hide();
    setTimeout(function(){refresh_countdown(obj, interval);}, interval*1000);
}


function show_navpath(imo, mmsi) {
    $.post('/vessel/get_vessel_navpath',
        {
         'imo': imo,
         'mmsi': mmsi,
        },
        function(data) {
            if (data['set_cookies_js']) {
                eval(data['set_cookies_js']);
            }
            if (data['res'] == 'FAILURE') {
            } else {
                var path = L.polyline(data['positions']).addTo(map);
                //map.fitBounds(path.getBounds());
            }
        }
    )
}

function add2myfleet(obj, imo, mmsi) {
    $.post('/vessel/update_user_fleet',
        {'action': 'add',
         'imo': imo,
         'mmsi': mmsi,
        },
        function(data) {
            if (data['set_cookies_js']) {
                eval(data['set_cookies_js']);
            }

            if (data['res'] == 'FAILURE') {
            } else {
                alert('added successfully');
            }
        }
    )
}

function del4myfleet(obj, imo, mmsi) {
    $.post('/vessel/update_user_fleet',
        {'action': 'delete',
         'imo': imo,
         'mmsi': mmsi,
        },
        function(data) {
            if (data['set_cookies_js']) {
                eval(data['set_cookies_js']);
            }

            if (data['res'] == 'FAILURE') {
            } else {
                alert('deleted successfully');
                $(obj).parent().parent().remove();
            }
        }
    )
}

function add2reminder(obj, imo, mmsi) {
    $.post('/vessel/update_vessel_reminder',
        {'action': 'add',
         'imo': imo,
         'mmsi': mmsi,
        },
        function(data) {
            if (data['set_cookies_js']) {
                eval(data['set_cookies_js']);
            }

            if (data['res'] == 'FAILURE') {
            } else {
                alert('added successfully');
            }
        }
    )
}

function add2creminder(obj, container) {
    $.post('/vessel/update_container_reminder',
        {'action': 'add',
         'container': container,
        },
        function(data) {
            if (data['set_cookies_js']) {
                eval(data['set_cookies_js']);
            }

            if (data['res'] == 'FAILURE') {
            } else {
                alert('added successfully');
            }
        }
    )
}
