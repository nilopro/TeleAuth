# TeleAuth

TeleAuth is a library that provides authentication functionality for Telegram bots.

## Features
- Admin authentication: Only authorized users can access certain functionality
- User authentication: Authorize users for a limited time
- Multiple store support: Use SQLite or JSON to store authorized users

## Installation

To install TeleAuth, simply use pip:

```bash
pip install teleauth
```

# Example

Here is a simple example of how to use TeleAuth with a Telegram bot:

```python
from teleauth import Auth, StoreType

auth = Auth([123456789], store_type=StoreType.SQLITE)

# Check if a user is an admin
auth.is_admin(123456789)  # True
auth.is_admin(987654321)  # False

# Check if a user is authenticated
auth.is_authenticated(123456789)  # True
auth.is_authenticated(987654321)  # False

# Authorize a user for 3 days and 2 hours
auth.authorize_user(987654321, days=3, hours=2)

# Check if the user is now authenticated
auth.is_authenticated(987654321)  # True

# Get a table with authorized users
print(auth.get_authorized_users_table())
"""
+----------+---------------------------+
| USER ID  | EXPIRES                   |
+----------+---------------------------+
| 123456789| Admin                     |
| 987654321| 01/01/2022 00:00          |
+----------+---------------------------+
"""

# Get the remaining time for a user
auth.remaining_time(987654321)  # (2, 23, 59)

# Revoke access for a user
auth.revoke_access(987654321)

# Check if the user is now authenticated
auth.is_authenticated(987654321)  # False

# Close the store when finished
auth.close()
```

# Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
