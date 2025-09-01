// main.js

document.addEventListener('DOMContentLoaded', () => {
    const userList = document.getElementById('user-list');
    const userForm = document.getElementById('user-form');
    const userIdInput = document.getElementById('user-id');
    const nameInput = document.getElementById('name-input');
    const mobileInput = document.getElementById('mobile-input');
    const addBtn = document.getElementById('add-btn');
    const updateMobile = document.getElementById('update-btn');
    const clearBtn = document.getElementById('clear-btn');
    const updateOnCallBtn = document.getElementById('update-oncall-btn');
    const scheduleForm = document.getElementById('schedule-form');
    const scheduleDatetimeInput = document.getElementById('schedule-datetime');
    const scheduleList = document.getElementById('schedule-list');

    // State to keep track of the selected user
    let selectedUser = null;

    // --- Core Functions ---

    // Function to fetch and display users
    async function fetchUsers() {
        try {
            const response = await fetch('/audssoncall/api/users');
            if (!response.ok) throw new Error('Failed to fetch users');
            const users = await response.json();
            
            userList.innerHTML = ''; // Clear existing options
            users.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id; // The value will be the user's ID
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

    // Change 'click' to 'change' for better usability with select elements.
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

    // Add Person button click event
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
            await fetchUsers(); // Refresh the list
            clearSelection();
            alert('User added successfully!');
        } catch (error) {
            console.error('Error adding user:', error);
            alert('Failed to add user.');
        }
    });

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
    

    // Function to select a user from the list
    function selectUser(user) {
        // Clear previous selection
        document.querySelectorAll('#user-list li').forEach(li => li.classList.remove('selected'));
        
        // Highlight the clicked user
        const selectedLi = userList.querySelector(`li[data-id="${user.id}"]`);
        if (selectedLi) {
            selectedLi.classList.add('selected');
        }
        
        // Populate the form fields
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
        document.querySelectorAll('#user-list li').forEach(li => li.classList.remove('selected'));
    }

    // --- Event Listeners ---

    // Form submission for Add/Update
    userForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = userIdInput.value;
        const name = nameInput.value;
        const mobile = mobileInput.value;

        if (id) {
            // Update an existing user
            try {
                const response = await fetch(`/audssoncall/api/users/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, mobile })
                });
                if (!response.ok) throw new Error('Failed to update user');
                await fetchUsers(); // Refresh the list
                clearSelection();
                alert('User updated successfully!');
            } catch (error) {
                console.error('Error updating user:', error);
                alert('Failed to update user.');
            }
        } else {
            // Add a new user
            try {
                const response = await fetch('/audssoncall/api/users', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, mobile })
                });
                if (!response.ok) throw new Error('Failed to add user');
                await fetchUsers(); // Refresh the list
                clearSelection();
                alert('User added successfully!');
            } catch (error) {
                console.error('Error adding user:', error);
                alert('Failed to add user.');
            }
        }
    });

    // Clear Selection button
    clearBtn.addEventListener('click', clearSelection);

    //Handle "Update Mobile#" buttons click
    updateMobile.addEventListener('click', async () => {
        if (!selectedUser) {
            alert('Please select a user to update the mobile number.');
            return;
        }

        const newMobile = prompt('Enter the new mobile number:', selectedUser.mobile);
        if (!newMobile) return;

        try {
            const response = await fetch(`/audssoncall/api/users/${selectedUser.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mobile: newMobile })
            });
            if (!response.ok) throw new Error('Failed to update mobile number');
            await fetchUsers(); // Refresh the list
            clearSelection();
            alert('Mobile number updated successfully!');
        } catch (error) {
            console.error('Error updating mobile number:', error);
            alert('Failed to update mobile number.');
        }
    });


    function showUpdateMobileModal(user) {
        modalMobileInput.value = user.mobile;
        modalOverlay.style.display = 'flex';
        // Add a one-time event listener for OK button
        const handleOkClick = async () => {
            const newMobile = modalMobileInput.value;
            if (!newMobile) {
                alert('Mobile number cannot be empty.');
                return;
            }
            
            try {
                const response = await fetch(`/audssoncall/api/users/${user.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: user.name, mobile: newMobile })
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
            } finally {
                modalOverlay.style.display = 'none'; // Hide the modal
                modalOkBtn.removeEventListener('click', handleOkClick); // Clean up
            }
        };

        modalOkBtn.addEventListener('click', handleOkClick);

        // Add a one-time event listener for Cancel button
        const handleCancelClick = () => {
            modalOverlay.style.display = 'none';
            modalOkBtn.removeEventListener('click', handleOkClick); // Clean up
            modalCancelBtn.removeEventListener('click', handleCancelClick);
        };
        modalCancelBtn.addEventListener('click', handleCancelClick);
    }

    // Handle "Update OnCall Now" button click
    // updateOnCallBtn.addEventListener('click', async () => {
    //     if (!selectedUser) {
    //         alert('Please select a user to update the On-Call number.');
    //         return;
    //     }

    //     const confirmUpdate = confirm(`Are you sure you want to update the SBC on-call number to ${selectedUser.mobile}?`);
    //     if (!confirmUpdate) return;

    //     try {
    //         const response = await fetch('/audssoncall/api/oncall/update', {
    //             method: 'POST',
    //             headers: { 'Content-Type': 'application/json' },
    //             body: JSON.stringify({ mobile: selectedUser.mobile })
    //         });
    //         if (!response.ok) throw new Error('Failed to update on-call number');
    //         const result = await response.json();
    //         console.log('Update result:', result);
    //         alert('On-Call number updated successfully!');
    //         fetchSbcStatus(); // Refresh SBC status
    //     } catch (error) {
    //         console.error('Error updating on-call:', error);
    //         alert('Failed to update On-Call number.');
    //     }
    // });

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

    // Schedule form submission
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
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    user_id: selectedUser.id,
                    scheduled_time: scheduledTime 
                })
            });
            if (!response.ok) throw new Error('Failed to schedule update');
            await fetchSchedules(); // Refresh the schedule list
            alert('Update scheduled successfully!');
        } catch (error) {
            console.error('Error scheduling update:', error);
            alert('Failed to schedule update.');
        }
    });

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

    // Initial data load on page load
    fetchUsers();
    fetchSbcStatus();
    fetchSchedules();
});