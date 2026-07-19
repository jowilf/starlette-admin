# Advanced 04: User Registration (CustomView + AuthProvider)

Demonstrates a public sign-up page for the admin: a `CustomView` renders a registration form that anyone can reach, creates the account in a `users` table with a hashed password, logs the new user in, and redirects into the admin. The login page checks credentials against the same table.

## What it shows

### `RegistrationAuthProvider`: database-backed login

- **`login`**: looks the user up by username and verifies the password against the stored bcrypt hash, then stores the user id in the session cookie.
- **`authenticate`**: reloads the user from the database on every request from the session's `user_id`.

### `RegistrationView`: public sign-up page

- A `CustomView` at `/admin/register` with `add_to_menu=False`.
- Overrides `index` with `@login_not_required` and `@route("", methods=["GET", "POST"])`. `@login_not_required` exempts the route from the auth check so unauthenticated visitors are not redirected to the login page. GET renders the form, POST validates it (username length and uniqueness, password length and confirmation), creates the `User`, writes `user_id` to the session, and redirects to the admin index.
- Renders `templates/register.html`, which extends the built-in `layout.html` with the header and sidebar blocked out, the same pattern as the built-in login page. The form includes `{{ csrf_input(request) }}` so it passes the admin's CSRF middleware.

### `templates/login.html`: a "Sign up" link on the login page

- Overrides the built-in login page with `{% extends "@starlette-admin/login.html" %}`. The `@starlette-admin/` prefix always resolves to the packaged templates, so an override file may share the name of the template it extends.
- Fills the `login_card_footer` block with a link to the registration page. The rest of the login page (form, logo, error handling) is inherited untouched.

### `UserView`: manage registered users

- `fields` lists only `id`, `username`, `full_name`, and `created_at`, so the password hash never appears in the list, detail, or forms.
- `can_create` / `can_edit` return `False`: accounts are only created through the registration page.

## Models

| Model | Key fields |
|---|---|
| `User` | `id`, `username` (unique), `full_name`, `password_hash`, `created_at` |

Passwords are hashed with [passlib](https://passlib.readthedocs.io/)'s `CryptContext`, using the `bcrypt` scheme.

## Run

```bash
cd examples/advanced/04-user-registration
uv run app.py
```

Then open <http://localhost:8000/admin/register>.

- Create an account: you are logged in immediately and land in the admin.
- Log out and sign back in at <http://localhost:8000/admin/> with the same credentials.
- The **Users** view lists every registered account (read-only, no password hash shown).
