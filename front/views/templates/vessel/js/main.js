function view(map, lat, lon, zoom) {
    if (zoom == undefined) zoom = 5;
    map.setView([lat, lon], zoom);

    L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
        minZoom: 2,
        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
}

function mark(map, lat, lon, heading, popup) {
    var marker = L.marker([lat, lon],
                          {icon: getIcon(heading)}).addTo(map);
    marker.bindPopup(popup);
    marker.on('click', function(e) {
        marker.openPopup();
    });
}

function getIcon(degree) {
    var region = parseInt(degree/45 + 0.5);
    if (region >= 360) region = 0;
    return L.icon({
        iconUrl: '/templates/vessel/img/my-icon-' + region * 45 + '.png',
        iconSize: [25, 25]
    });
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
