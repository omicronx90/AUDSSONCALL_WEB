// main.js

document.addEventListener('DOMContentLoaded', () => {
    const userList = document.getElementById('user-list');
    const userForm = document.getElementById('user-form');
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
    const removeBtn = document.getElementById('remove-btn');

    // State to keep track of the selected user
    let selectedUser = null;

    // --- Core Functions ---

    // Function to fetch and display users
    async function fetchUsers() {
        try {
            const response = await fetch('/audssoncall/api/users');
            if (!response.ok) throw new Error('Failed to fetch users');
            const users = await response.json();
            
            userList.innerHTML = '';
            users.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.textContent = `${user.name} - ${user.mobile}`;
                option.dataset.name = user.name;
                option.dataset.mobile = user.mobile;
                userList.appendChild(option);
            });
        } catch (error) {
            console.error('Error fetching users:', error);
            alert('Failed to load user list.');
        }
    }

    // Function to select a user from the list
    function selectUser(user) {
        userIdInput.value = user.id;
        nameInput.value = user.name;
        mobileInput.value = user.mobile;
        selectedUser = user;
    }

    // Function to clear the form and selection
    function clearSelection() {
        userIdInput.value = '';
        nameInput.value = '';
        mobileInput.value = '';
        selectedUser = null;
        userList.selectedIndex = -1; // Deselects any option in the list box
    }

    function setDefaultScheduleTime() {
        const now = new Date();

        // Get date components
        const year = now.getFullYear();
        const month = (now.getMonth() + 1).toString().padStart(2, '0');
        const day = now.getDate().toString().padStart(2, '0');
        
        // Define the default time
        const defaultTime = '12:00'; 

        // Combine into the required 'YYYY-MM-DDTHH:mm' format
        const defaultDateTime = `${year}-${month}-${day}T${defaultTime}`;

        // Set the value of the input field
        scheduleDatetimeInput.value = defaultDateTime;
    }

    // Function to fetch and display SBC on-call status
    async function fetchSbcStatus() {
        const perthStatus = document.getElementById('sbc-status-perth').querySelector('span');
        const ppsStatus = document.getElementById('sbc-status-pps').querySelector('span');

        perthStatus.textContent = 'Checking...';
        ppsStatus.textContent = 'Checking...';
        
        try {
            const response = await fetch('/audssoncall/api/oncall');
            if (!response.ok) throw new Error('Failed to fetch SBC status');
            const status = await response.json();
            
            const perthData = status.find(item => item.host.startsWith('pernetgw01'));
            const ppsData = status.find(item => item.host.startsWith('parnetgw01'));

            perthStatus.textContent = perthData ? perthData.number || 'N/A' : 'Error';
            ppsStatus.textContent = ppsData ? ppsData.number || 'N/A' : 'Error';
            
            perthStatus.className = perthData && perthData.number ? 'success' : 'error';
            ppsStatus.className = ppsData && ppsData.number ? 'success' : 'error';

        } catch (error) {
            console.error('Error fetching SBC status:', error);
            perthStatus.textContent = 'Error';
            ppsStatus.textContent = 'Error';
            perthStatus.className = 'error';
            ppsStatus.className = 'error';
        }
    }

    // Fetch and display schedules
    async function fetchSchedules() {
        try {
            const response = await fetch('/audssoncall/api/schedules');
            if (!response.ok) throw new Error('Failed to fetch schedules');
            const schedules = await response.json();
            scheduleList.innerHTML = '';
            schedules.forEach(schedule => {
                const li = document.createElement('li');
                const scheduledDateTime = new Date(schedule.scheduled_time).toLocaleString();
                li.textContent = `${schedule.user_name} scheduled for ${scheduledDateTime}`;
                scheduleList.appendChild(li);
            });
        } catch (error) {
            console.error('Error fetching schedules:', error);
        }
    }

    // --- Event Listeners ---
    
    // Listen for changes on the user list box
    userList.addEventListener('change', () => {
        const selectedOption = userList.options[userList.selectedIndex];
        if (selectedOption) {
            const user = {
                id: selectedOption.value,
                name: selectedOption.dataset.name,
                mobile: selectedOption.dataset.mobile
            };
            selectUser(user);
        }
    });

    // Handle "Add Person" button click
    addBtn.addEventListener('click', async () => {
        const name = nameInput.value;
        const mobile = mobileInput.value;

        if (!name || !mobile) {
            alert('Please fill in both name and mobile number.');
            return;
        }

        try {
            const response = await fetch('/audssoncall/api/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, mobile })
            });
            if (!response.ok) throw new Error('Failed to add user');
            
            await fetchUsers();
            clearSelection();
            alert('User added successfully!');
        } catch (error) {
            console.error('Error adding user:', error);
            alert('Failed to add user.');
        }
    });

    removeBtn.addEventListener('click', async () => {
        const id = userIdInput.value;
        const name = nameInput.value;

        if (!id) {
            alert('Please select a user to remove.');
            return;
        }

        const confirmDelete = confirm(`Are you sure you want to permanently remove ${name}? This will also delete any scheduled jobs for this user.`);
        if (!confirmDelete) {
            return;
        }

        try {
            const response = await fetch(`/audssoncall/api/users/${id}`, {
                method: 'DELETE',
            });
            
            const result = await response.json();
            alert(result.message);
            
            if (response.ok) {
                await fetchUsers();
                clearSelection();
                await fetchSchedules(); // Also refresh the schedules list
            }
        } catch (error) {
            console.error('Error removing user:', error);
            alert('Failed to remove user.');
        }
    });

    // Handle "Update Mobile#" button click
    updateBtn.addEventListener('click', async () => {
        const id = userIdInput.value;
        const name = nameInput.value;
        const mobile = mobileInput.value;

        if (!id) {
            alert('Please select a user to update.');
            return;
        }
        
        if (!name || !mobile) {
            alert('Name and mobile fields cannot be empty.');
            return;
        }

        try {
            const response = await fetch(`/audssoncall/api/users/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, mobile })
            });
            
            const result = await response.json();
            alert(result.message);
            
            if (response.ok) {
                await fetchUsers();
                clearSelection();
            }
        } catch (error) {
            console.error('Error updating user:', error);
            alert('Failed to update user.');
        }
    });
    
    // Handle "Clear Selection" button click
    clearBtn.addEventListener('click', clearSelection);

    // Handle "Update OnCall Now" button click
    updateOnCallBtn.addEventListener('click', async () => {
        if (!selectedUser) {
            alert('Please select a user to update the On-Call number.');
            return;
        }

        const confirmUpdate = confirm(`Are you sure you want to update the SBC on-call number to ${selectedUser.mobile}?`);
        if (!confirmUpdate) return;

        try {
            const response = await fetch('/audssoncall/api/oncall/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mobile: selectedUser.mobile })
            });
            if (!response.ok) throw new Error('Failed to update on-call number');
            const result = await response.json();
            console.log('Update result:', result);
            alert('On-Call number updated successfully!');
            fetchSbcStatus(); // Refresh SBC status
        } catch (error) {
            console.error('Error updating on-call:', error);
            alert('Failed to update On-Call number.');
        }
    });

    // Handle "Schedule" form submission
    scheduleForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!selectedUser) {
            alert('Please select a user to schedule an update.');
            return;
        }

        const scheduledTime = scheduleDatetimeInput.value;
        if (!scheduledTime) {
            alert('Please select a date and time.');
            return;
        }

        try {
            const response = await fetch('/audssoncall/api/schedule', {
                method: 'POST',
                // This is the crucial fix: Ensure the Content-Type header is set
                headers: {
                    'Content-Type': 'application/json'
                },
                // Stringify the JavaScript object to send it as a JSON string
                body: JSON.stringify({ 
                    user_id: selectedUser.id,
                    scheduled_datetime: scheduledTime 
                })
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to schedule update');
            }
            await fetchSchedules(); // Refresh the schedule list
            alert('Update scheduled successfully!');
        } catch (error) {
            console.error('Error scheduling update:', error);
            alert('Failed to schedule update: ' + error.message);
        }
    });

     // --- Function to fetch and display schedules ---
    // async function fetchSchedules() {
    //     try {
    //         const response = await fetch('/audssoncall/api/schedule');
    //         if (!response.ok) throw new Error('Failed to fetch schedules');
    //         const schedules = await response.json();
            
    //         scheduleList.innerHTML = '';
    //         if (schedules.length === 0) {
    //             const li = document.createElement('li');
    //             li.textContent = 'No upcoming schedules.';
    //             scheduleList.appendChild(li);
    //             return;
    //         }

    //         schedules.forEach(schedule => {
    //             const li = document.createElement('li');
    //             const scheduledDateTime = new Date(schedule.scheduled_datetime).toLocaleString();
    //             li.innerHTML = `
    //                 <span>
    //                     ${schedule.name} scheduled for ${scheduledDateTime}
    //                 </span>
    //                 <button class="delete-schedule-btn" data-id="${schedule.id}">Delete</button>
    //             `;
    //             scheduleList.appendChild(li);
    //         });
    //     } catch (error) {
    //         console.error('Error fetching schedules:', error);
    //         alert('Failed to load schedules.');
    //     }
    // }

    // --- Function to fetch and display schedules ---
    async function fetchSchedules() {
        try {
            const response = await fetch('/audssoncall/api/schedule');
            if (!response.ok) throw new Error('Failed to fetch schedules');
            const schedules = await response.json();
            
            scheduleList.innerHTML = '';
            if (schedules.length === 0) {
                const li = document.createElement('li');
                li.textContent = 'No upcoming schedules.';
                scheduleList.appendChild(li);
                return;
            }

            schedules.forEach(schedule => {
                const li = document.createElement('li');
                const scheduledDateTime = new Date(schedule.scheduled_datetime).toLocaleString();
                li.innerHTML = `
                    <span>
                        ${schedule.name} scheduled for ${scheduledDateTime}
                    </span>
                    <button class="delete-schedule-btn" data-id="${schedule.id}">X</button>
                `;
                scheduleList.appendChild(li);
            });
        } catch (error) {
            console.error('Error fetching schedules:', error);
            alert('Failed to load schedules.');
        }
    }

    // --- New Event Listener for Schedule Deletion ---
    scheduleList.addEventListener('click', async (e) => {
        if (e.target.classList.contains('delete-schedule-btn')) {
            const scheduleId = e.target.dataset.id;
            const confirmDelete = confirm('Are you sure you want to delete this scheduled job?');
            
            if (!confirmDelete) {
                return;
            }

            try {
                const response = await fetch(`/audssoncall/api/schedule/${scheduleId}`, {
                    method: 'DELETE',
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to delete schedule');
                }

                alert('Scheduled job deleted successfully!');
                fetchSchedules(); // Refresh the list
            } catch (error) {
                console.error('Error deleting schedule:', error);
                alert('Failed to delete schedule: ' + error.message);
            }
        }
    });

    // Initial data load on page load
    fetchUsers();
    fetchSbcStatus();
    fetchSchedules();
    setDefaultScheduleTime(); 
});