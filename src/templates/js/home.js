var latest_violation = document.getElementById('latest-violation');
var all_violations = document.getElementById('violations-list');

function addViolation(violation) {
    let li = document.getElementById('violation-' + violation.drone.serial_number);
    if (li) {
        li.remove();
    }

    li = document.createElement('li');
    li.id = 'violation-' + violation.drone.serial_number;
    let div = document.createElement('div');
    div.className = 'violation';
    div.innerHTML = `
        <h4> Serial Number: ${violation.drone.serial_number} </h4>
        <p> Pilot: ${violation.pilot.first_name} ${violation.pilot.last_name} </p>
        <p> Distance: ${violation.drone.distance} </p>
        <p> Email: ${violation.pilot.email} </p>
        <p> Phone Number: ${violation.pilot.phone_number} </p>
        <p> Position: (${violation.drone.position_x}, ${violation.drone.position_y}) </p>
        <p> Time: ${violation.timestamp} </p>
    `;

    latest_violation.innerHTML = div.innerHTML;
    li.appendChild(div);
    all_violations.appendChild(li);

    setTimeout(function() {
        li.remove();
        if (latest_violation.innerHTML === div.innerHTML) {
            latest_violation.innerHTML = '<p> No violations yet </p>';
        }
    }, violation.delete_after * 1000);
}

function removeViolation(violation) {
    var element = document.getElementById('violation-' + violation.drone.serial_number);
    if (element) {
        element.remove();
    }

    var last_violation = document.getElementById('last-violation');
    if (last_violation && last_violation_serial == violation.drone.serial_number) {
        last_violation.innerHTML = '<p> No violations yet </p>';
    }
}

var socket = io();
socket.emit('request_cached_violations');

socket.on('on_violation', function(drone_data) {
    console.log(drone_data);
    addViolation(drone_data);
});

socket.on('on_violation_expired', function(drone_data) {
    // removeViolation(drone_data);
});

socket.on('on_receive_cached_violations', function(arr_drone_data) {
    console.log(arr_drone_data);
    arr_drone_data.forEach(function(drone_data) {
        addViolation(drone_data);
    });
});