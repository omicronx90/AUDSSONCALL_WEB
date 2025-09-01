//main.js

document.addEventListener('DOMContentLoaded', () => {
    // --- DOM ELEMENT REFERENCES ---
    
    // --- BASE PATH CONFIGURATION ---
    const API_BASE = '/audssoncall/api'; // Or just '/api' if hosted at root

    const userList = document.getElementById('user-list');
    const userIdInput = document.getElementById('user-id');
    const nameInput = document.getElementById('name-input');
    const mobileInput = document.getElementById('mobile-input');
    
    const addBtn = document.getElementById('add-btn');
    const updateBtn = document.getElementById('update-btn');
    const clearBtn = document.getElementById('clear-btn');
    const updateOnCallBtn = document.getElementById('update-oncall-btn');

    const scheduleForm = document.getElementById('schedule-form');
    const scheduleDatetimeInput = document.getElementById('schedule-datetime');
    const scheduleList = document.getElementById('schedule-list');

    const sbcStatusPerth = document.querySelector('#sbc-status-perth span');
    const sbcStatusPps = document.querySelector('#sbc-status-pps span');

    // --- STATE MANAGEMENT ---
    let selectedUserId = null;

    // --- API HELPER ---
    // const api = {
    //     get: (url) => fetch(url).then(res => res.json()),
    //     post: (url, data) => fetch(url, {
    //         method: 'POST',
    //         headers: { 'Content-Type': 'application/json' },
    //         body: JSON.stringify(data)
    //     }).then(res => res.json()),
    //     put: (url, data) => fetch(url, {
    //         method: 'PUT',
    //         headers: { 'Content-Type': 'application/json' },
    //         body: JSON.stringify(data)
    //     }).then(res => res.json()),
    // };
    const api = {
        get: (path) => fetch(`${API_BASE}${path}`).then(res => res.json()),
        post: (path, data) => fetch(`${API_BASE}${path}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).then(res => res.json()),
        put: (path, data) => fetch(`${API_BASE}${path}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).then(res => res.json()),
    };

    // --- CORE FUNCTIONS ---

    const clearForm = () => {
        userIdInput.value = '';
        nameInput.value = '';
        mobileInput.value = '';
        selectedUserId = null;
        document.querySelectorAll('#user-list li.selected').forEach(li => li.classList.remove('selected'));
    };

    const populateUsers = async () => {
        try {
            const users = await api.get('/users');
            userList.innerHTML = '';
            users.forEach(user => {
                const li = document.createElement('li');
                li.textContent = `${user.name} - ${user.mobile}`;
                li.dataset.id = user.id;
                li.dataset.name = user.name;
                li.dataset.mobile = user.mobile;
                userList.appendChild(li);
            });
        } catch (error) {
            console.error('Failed to load users:', error);
            alert('Error: Could not load users.');
        }
    };

    const updateSBCStatus = async () => {
        try {
            const statuses = await api.get('/oncall');
            
            // Find the status object for each SBC from the returned list
            const perthStatus = statuses.find(s => s.host === 'pernetgw01.transalta.org');
            const ppsStatus = statuses.find(s => s.host === 'parnetgw01.transalta.org');

            // Update Perth SBC status
            if (perthStatus) {
                sbcStatusPerth.className = perthStatus.status;
                sbcStatusPerth.textContent = perthStatus.status === 'success' ? perthStatus.number : `Error: ${perthStatus.message}`;
            } else {
                // Handle case where status for a specific host is not found
                sbcStatusPerth.className = 'error';
                sbcStatusPerth.textContent = 'Error: Status not available.';
            }

            // Update Parkeston SBC status
            if (ppsStatus) {
                sbcStatusPps.className = ppsStatus.status;
                sbcStatusPps.textContent = ppsStatus.status === 'success' ? ppsStatus.number : `Error: ${ppsStatus.message}`;
            } else {
                // Handle case where status for a specific host is not found
                sbcStatusPps.className = 'error';
                sbcStatusPps.textContent = 'Error: Status not available.';
            }
            
        } catch (error) {
            console.error('Failed to update SBC status:', error);
            sbcStatusPerth.className = 'error';
            sbcStatusPerth.textContent = 'Failed to connect to backend.';
            sbcStatusPps.className = 'error';
            sbcStatusPps.textContent = 'Failed to connect to backend.';
        }
    };

    // --- EVENT HANDLERS ---
    userList.addEventListener('click', (e) => {
        if (e.target.tagName === 'LI') {
            clearForm(); // Clear previous selection
            e.target.classList.add('selected');
            userIdInput.value = e.target.dataset.id;
            nameInput.value = e.target.dataset.name;
            mobileInput.value = e.target.dataset.mobile;
            selectedUserId = e.target.dataset.id;
        }
    });
    
    addBtn.addEventListener('click', async () => {
        const name = nameInput.value.trim();
        const mobile = mobileInput.value.trim();
        if (!name || !mobile) {
            return alert('Please enter both name and mobile number.');
        }
        await api.post('/users', { name, mobile });
        clearForm();
        populateUsers();
    });

    updateBtn.addEventListener('click', async () => {
        if (!selectedUserId) {
            return alert('Please select a user to update.');
        }
        const mobile = mobileInput.value.trim();
        if (!mobile) {
            return alert('Mobile number cannot be empty.');
        }
        await api.put(`/users/${selectedUserId}`, { mobile });
        clearForm();
        populateUsers();
    });

    updateOnCallBtn.addEventListener('click', async () => {
        const mobile = mobileInput.value.trim();
        if (!mobile) {
            return alert('Please select a user or enter a mobile number to update.');
        }
        updateOnCallBtn.textContent = 'Updating...';
        updateOnCallBtn.disabled = true;

        const result = await api.post('/oncall', { mobile });
        alert('OnCall update process finished. Check statuses below for results.');
        
        updateOnCallBtn.textContent = 'Update OnCall Now';
        updateOnCallBtn.disabled = false;
        await updateSBCStatus();
    });

    scheduleForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const scheduled_datetime = scheduleDatetimeInput.value;
        if (!selectedUserId) {
            return alert('Please select a user to schedule.');
        }
        if (!scheduled_datetime) {
            return alert('Please select a date and time.');
        }
        
        await api.post('/schedules', { user_id: selectedUserId, scheduled_datetime });
        alert('Update scheduled successfully!');
        scheduleDatetimeInput.value = '';
        populateSchedules();
    });
    
    clearBtn.addEventListener('click', clearForm);

    // --- INITIALIZATION ---
    const initializeApp = () => {
        populateUsers();
        updateSBCStatus();
        populateSchedules();
    };

    initializeApp();
});