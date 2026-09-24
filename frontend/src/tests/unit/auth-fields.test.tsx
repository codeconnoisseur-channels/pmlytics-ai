import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { AuthFields } from '@/components/auth/AuthFields';

describe('AuthFields', () => {
  it('shows and updates the complete new-password requirements', () => {
    render(<AuthFields passwordMode="new" />);

    const password = screen.getByLabelText('Password');
    expect(password).toHaveAttribute('minlength', '8');
    expect(password).toHaveAttribute('pattern', expect.stringContaining('(?=.*[A-Z])'));
    expect(screen.getByText('8 or more characters')).toBeInTheDocument();
    expect(screen.getByText('One uppercase letter')).toBeInTheDocument();
    expect(screen.getByText('One lowercase letter')).toBeInTheDocument();
    expect(screen.getByText('One number')).toBeInTheDocument();

    fireEvent.change(password, { target: { value: 'GoodPass1' } });
    expect(screen.getByRole('button', { name: 'Show password' })).toBeInTheDocument();
  });

  it('does not impose sign-up rules on an existing account password', () => {
    render(<AuthFields />);

    const password = screen.getByLabelText('Password');
    expect(password).not.toHaveAttribute('pattern');
    expect(screen.queryByText(/Your password must include/i)).not.toBeInTheDocument();
  });

  it('allows users to reveal and hide the password', () => {
    render(<AuthFields passwordMode="new" />);

    const password = screen.getByLabelText('Password');
    fireEvent.click(screen.getByRole('button', { name: 'Show password' }));
    expect(password).toHaveAttribute('type', 'text');
    fireEvent.click(screen.getByRole('button', { name: 'Hide password' }));
    expect(password).toHaveAttribute('type', 'password');
  });
});
