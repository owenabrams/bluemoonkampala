var overlay;
USGSOverlay.prototype = new google.maps.OverlayView();

// Initialize the map and the custom overlay.
var a = 42.5, b = -3.56;
var myLatlng = new google.maps.LatLng(a, b);
var myLatlng2 = new google.maps.LatLng(41, -3);

function initialize() {
    var mapOptions = {
        zoom: window.innerWidth < 768 ? 5 : 6,
        center: myLatlng,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        backgroundColor: '#FFF',
        disableDefaultUI: true,
        draggable: true,
        scaleControl: true,
        scrollwheel: false,
        styles: [{
                "featureType": "water",
                "elementType": "geometry",
                "stylers": [{
                        "color": "#52a5d2"
                    }]
            }, {
                "featureType": "landscape",
                "stylers": [{
                        "visibility": "off"
                    }]
            }, {
                "featureType": "road",
                "stylers": [{
                        "visibility": "off"
                    }]
            }, {
                "featureType": "administrative.countries",
                "stylers": [{
                        "visibility": "off"
                    }]
            }, {
                "featureType": "poi",
                "stylers": [{
                        "visibility": "off"
                    }]
            }, {
                "elementType": "labels",
                "stylers": [{
                        "visibility": "off"
                    }]
            }, {}]
    };

    var map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);
    var infowindow = false;
    geocoder = new google.maps.Geocoder();

    function codeAddress(address, title, description) {
        geocoder.geocode({
            'address': address
        }, function (results, status) {
            if (status == google.maps.GeocoderStatus.OK) {
                if(infowindow) {
                    infowindow.close();
                }
                infowindow = new google.maps.InfoWindow();
                var marker = new google.maps.Marker({
                    map: map,
                    icon: {
                        url: "img/app/layout/map_marker.png"
                    },
                    position: results[0].geometry.location
                });
                google.maps.event.addListener(marker, 'click', (function (marker, i) {
                    return function () {
                        var content = '<div style="padding: 10px;"><p class="mapTitle">' + title + '</p>';
                        content += '<p class="mapCity">' + address + '</p>';
                        content += '<p class="mapDescription">' + description + '</p></div>';
                        infowindow.setContent(content);
                        infowindow.open(map, marker);
                    };
                })(marker));
            } else {
                console.log('Geocode was not successful for the following reason: ' + status);
            }
        });
    }

    for (var i = 0; i < data.length; i++) {
        codeAddress(data[i][0], data[i][1], data[i][2]);
    }


    var roadsLayer = [{
            featureType: 'all',
            stylers: [{
                    visibility: 'off'
                }]
        }, {
            featureType: 'road',
            stylers: [{
                    visibility: 'off'
                }]
        }, {
            featureType: 'label',
            stylers: [{
                    visibility: 'on'
                }]
        }];

    var roadsType = new google.maps.StyledMapType(roadsLayer, {
        name: 'roads'
    });
    map.overlayMapTypes.push(roadsType);
}

function USGSOverlay(bounds, image, map) {
    this.bounds_ = bounds;
    this.image_ = image;
    this.map_ = map;
    this.div_ = null;
    this.setMap(map);
}

USGSOverlay.prototype.onAdd = function () {
    var div = document.createElement('div');
    div.style.borderStyle = 'none';
    div.style.borderWidth = '0px';
    div.style.position = 'absolute';
    var img = document.createElement('img');
    img.src = this.image_;
    img.style.width = '100%';
    img.style.height = '100%';
    img.style.position = 'absolute';
    div.appendChild(img);
    this.div_ = div;
    var panes = this.getPanes();
    panes.overlayLayer.appendChild(div);
};
USGSOverlay.prototype.draw = function () {
    var overlayProjection = this.getProjection();
    var sw = overlayProjection.fromLatLngToDivPixel(this.bounds_.getSouthWest());
    var ne = overlayProjection.fromLatLngToDivPixel(this.bounds_.getNorthEast());
    var div = this.div_;
    div.style.left = sw.x + 'px';
    div.style.top = ne.y + 'px';
    div.style.width = (ne.x - sw.x) + 'px';
    div.style.height = (sw.y - ne.y) + 'px';
};
USGSOverlay.prototype.onRemove = function () {
    this.div_.parentNode.removeChild(this.div_);
    this.div_ = null;
};