import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import { userEvent } from '@testing-library/user-event';
import LoginPage from './+page.svelte';

describe('Login Page', () => {
	beforeEach(() => {
		vi.resetAllMocks();
	});

	it('should render login form with username and password fields', async () => {
		render(LoginPage);

		expect(screen.getByLabelText(/username/i)).toBeDefined();
		expect(screen.getByLabelText(/password/i)).toBeDefined();
		expect(screen.getByRole('button', { name: /login/i })).toBeDefined();
	});

	it('should allow user to type username and password', async () => {
		const user = userEvent.setup();
		render(LoginPage);

		const usernameInput = screen.getByLabelText(/username/i) as HTMLInputElement;
		const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement;

		await user.type(usernameInput, 'testuser');
		await user.type(passwordInput, 'testpass');

		expect(usernameInput.value).toBe('testuser');
		expect(passwordInput.value).toBe('testpass');
	});
});
