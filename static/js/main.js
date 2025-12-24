// Main JavaScript functionality for IT Ticketing System

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                if (message.parentNode) {
                    message.parentNode.removeChild(message);
                }
            }, 300);
        }, 5000);
    });

    // Form validation for ticket submission
    const ticketForm = document.querySelector('.ticket-form');
    if (ticketForm) {
        ticketForm.addEventListener('submit', function(e) {
            const description = ticketForm.querySelector('textarea[name="problem_description"]');
            if (description && description.value.trim().length < 10) {
                e.preventDefault();
                alert('Please provide a more detailed problem description (at least 10 characters).');
                description.focus();
                return false;
            }
        });
    }

    // Character counter for problem description
    const problemDescription = document.querySelector('textarea[name="problem_description"]');
    if (problemDescription) {
        const counter = document.createElement('div');
        counter.className = 'char-counter';
        counter.style.cssText = 'font-size: 12px; color: #6c757d; text-align: right; margin-top: 5px;';
        problemDescription.parentNode.insertBefore(counter, problemDescription.nextSibling);
        
        function updateCounter() {
            const length = problemDescription.value.length;
            counter.textContent = `${length} characters`;
            
            if (length < 10) {
                counter.style.color = '#dc3545';
            } else if (length > 500) {
                counter.style.color = '#ffc107';
            } else {
                counter.style.color = '#28a745';
            }
        }
        
        problemDescription.addEventListener('input', updateCounter);
        updateCounter(); // Initial count
    }

    // Confirm before closing tickets
    const closeTicketForms = document.querySelectorAll('form[action*="update_ticket"] input[value="Closed"]');
    closeTicketForms.forEach(function(input) {
        const form = input.closest('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                if (input.value === 'Closed') {
                    const confirmed = confirm('Are you sure you want to close this ticket? This action will notify the user that their issue has been resolved.');
                    if (!confirmed) {
                        e.preventDefault();
                        return false;
                    }
                }
            });
        }
    });

    // Dashboard search functionality
    const searchInput = document.querySelector('#ticket-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const tickets = document.querySelectorAll('.ticket-card');
            
            tickets.forEach(function(ticket) {
                const searchableText = ticket.textContent.toLowerCase();
                if (searchableText.includes(searchTerm)) {
                    ticket.style.display = 'block';
                } else {
                    ticket.style.display = 'none';
                }
            });
        });
    }

    // Auto-refresh dashboard every 30 seconds if on dashboard page
    if (window.location.pathname === '/dashboard') {
        let refreshInterval = setInterval(function() {
            // Only refresh if user is still on the page and page is visible
            if (!document.hidden) {
                const xhr = new XMLHttpRequest();
                xhr.open('GET', window.location.href, true);
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4 && xhr.status === 200) {
                        // Update ticket counts in header
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(xhr.responseText, 'text/html');
                        const newStats = doc.querySelector('.stats');
                        const currentStats = document.querySelector('.stats');
                        
                        if (newStats && currentStats) {
                            currentStats.innerHTML = newStats.innerHTML;
                        }
                    }
                };
                xhr.send();
            }
        }, 30000); // 30 seconds
        
        // Clear interval when leaving page
        window.addEventListener('beforeunload', function() {
            clearInterval(refreshInterval);
        });
    }

    // Copy ticket ID to clipboard functionality
    const ticketIds = document.querySelectorAll('.ticket-id');
    ticketIds.forEach(function(ticketId) {
        ticketId.style.cursor = 'pointer';
        ticketId.title = 'Click to copy ticket ID';
        
        ticketId.addEventListener('click', function() {
            const text = this.textContent.replace('#', '');
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(text).then(function() {
                    showToast('Ticket ID copied to clipboard!');
                }).catch(function() {
                    fallbackCopyToClipboard(text);
                });
            } else {
                fallbackCopyToClipboard(text);
            }
        });
    });

    // Fallback copy function for older browsers
    function fallbackCopyToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            showToast('Ticket ID copied to clipboard!');
        } catch (err) {
            showToast('Failed to copy ticket ID', 'error');
        }
        
        document.body.removeChild(textArea);
    }

    // Toast notification function
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: ${type === 'success' ? '#28a745' : '#dc3545'};
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        // Fade in
        setTimeout(() => toast.style.opacity = '1', 10);
        
        // Fade out and remove
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }

    // Email validation enhancement
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            const email = this.value.trim();
            if (email && !isValidEmail(email)) {
                this.setCustomValidity('Please enter a valid email address');
                this.reportValidity();
            } else {
                this.setCustomValidity('');
            }
        });
    });

    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + / for help
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            showKeyboardShortcuts();
        }
        
        // ESC to close modals or go back
        if (e.key === 'Escape') {
            const backButton = document.querySelector('a[href*="dashboard"], a[href*="back"]');
            if (backButton && window.location.pathname !== '/dashboard') {
                window.location.href = backButton.href;
            }
        }
    });

    function showKeyboardShortcuts() {
        const shortcuts = `
        Keyboard Shortcuts:
        • Ctrl/Cmd + / : Show this help
        • ESC : Go back (when not on dashboard)
        • Click ticket ID : Copy to clipboard
        `;
        alert(shortcuts);
    }

    // Enhanced form submission with loading states
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('input[type="submit"], button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.value || submitBtn.textContent;
                submitBtn.disabled = true;
                
                if (submitBtn.tagName === 'INPUT') {
                    submitBtn.value = 'Processing...';
                } else {
                    submitBtn.textContent = 'Processing...';
                }
                
                // Re-enable after 10 seconds as fallback
                setTimeout(function() {
                    submitBtn.disabled = false;
                    if (submitBtn.tagName === 'INPUT') {
                        submitBtn.value = originalText;
                    } else {
                        submitBtn.textContent = originalText;
                    }
                }, 10000);
            }
        });
    });

    // Initialize tooltips for remote access badges
    const remoteBadges = document.querySelectorAll('.remote-badge');
    remoteBadges.forEach(function(badge) {
        badge.title = 'User has authorized remote desktop access for this ticket';
    });

    // Status color coding enhancement
    const statusElements = document.querySelectorAll('.ticket-status, .ticket-status-badge');
    statusElements.forEach(function(element) {
        const status = element.textContent.trim().toLowerCase();
        element.setAttribute('data-status', status.replace(' ', '-'));
    });
});

// Utility function to format dates in a user-friendly way
function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes} minute${diffInMinutes === 1 ? '' : 's'} ago`;
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours} hour${diffInHours === 1 ? '' : 's'} ago`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays} day${diffInDays === 1 ? '' : 's'} ago`;
    
    return date.toLocaleDateString();
}

// Console welcome message (for IT staff debugging)
console.log(`
🎓 School IT Helpdesk System
============================
Version: 1.0.0
Environment: ${window.location.hostname === 'localhost' ? 'Development' : 'Production'}
Build: ${new Date().getFullYear()}

For support, contact the system administrator.
`);
