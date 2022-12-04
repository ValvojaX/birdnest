var latestViolation = document.getElementById('latest-violation');
var allViolations = document.getElementById('violations-list');

function buildViolationContent(violation) {
    return `
        <h4> Serial Number: ${violation.drone.serial_number} </h4>
        <p> Pilot: ${violation.pilot.first_name} ${violation.pilot.last_name} </p>
        <p> Pilot ID: ${violation.pilot.pilot_id} </p>
        <p> Distance: ${violation.drone.distance} </p>
        <p> Email: ${violation.pilot.email} </p>
        <p> Phone Number: ${violation.pilot.phone_number} </p>
        <p> Position: (${violation.drone.position_x}, ${violation.drone.position_y}) </p>
        <p> Time: ${violation.timestamp} </p>
    `;
}

function updateLatestViolation(violation) {
    let violationCount = allViolations.children.length;
    if (violationCount) {
        latestViolation.innerHTML = allViolations.children[violationCount - 1].children[0].innerHTML;
    }
    else {
        latestViolation.innerHTML = '<p> No violations yet </p>';
    }
}

function buildViolationListItem(violation) {
    let listItem = document.createElement('li');
    listItem.id = 'violation-' + violation.drone.serial_number;

    let div = document.createElement('div');
    div.className = 'violation';
    div.innerHTML = buildViolationContent(violation);
    listItem.appendChild(div);

    return listItem;
}

function buildLatestViolation(violation) {
    let div = document.createElement('div');
    div.id = 'latest-violation';
    div.className = 'violation';
    div.innerHTML = buildViolationContent(violation);
    return div;
}

function removeOldViolation(violation) {
    let listItem = document.getElementById('violation-' + violation.drone.serial_number);
    if (listItem) {
        listItem.remove();
    }
}

function addViolation(violation) {
    removeOldViolation(violation);

    let listItem = buildViolationListItem(violation);
    allViolations.appendChild(listItem);

    let latestViolation = buildLatestViolation(violation);
    latestViolation.innerHTML = latestViolation.innerHTML;

    updateLatestViolation(violation);

    setTimeout(function() {
        listItem.remove();
        updateLatestViolation(violation);
    }, violation.delete_after * 1000);
}

var socket = io();
socket.emit('request_cached_violations');

socket.on('on_violation', function(drone_data) {
    console.log(drone_data);
    addViolation(drone_data);
});

socket.on('on_receive_cached_violations', function(arr_drone_data) {
    console.log(arr_drone_data);
    arr_drone_data.forEach(function(drone_data) {
        addViolation(drone_data);
    });
});