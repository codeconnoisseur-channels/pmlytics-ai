import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { fireEvent, render } from '@testing-library/react';
import { AppShell } from '@/components/layout/AppShell';
import { Providers } from '@/app/providers';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  usePathname: () => '/investigations',
  useRouter: () => ({ push: vi.fn() }),
}));

describe('AppShell Component', () => {
  it('renders application brand, header, sidebar navigation, and main content', () => {
    const { getByText, getByRole, getByTestId } = render(
      <Providers>
        <AppShell headerTitle="Test Workspace">
          <div data-testid="workspace-content">Workspace Interior</div>
        </AppShell>
      </Providers>
    );

    // Header elements
    expect(getByText(/PMLytics/i)).toBeInTheDocument();
    expect(getByText('Test Workspace')).toBeInTheDocument();

    // Sidebar navigation
    expect(getByRole('link', { name: /investigations/i })).toBeInTheDocument();

    // Main content
    expect(getByTestId('workspace-content')).toBeInTheDocument();
  });

  it('toggles sidebar collapse state and persists to localStorage', () => {
    const { getByLabelText } = render(
      <Providers>
        <AppShell>
          <div>Content</div>
        </AppShell>
      </Providers>
    );

    const collapseBtn = getByLabelText('Collapse sidebar');
    expect(collapseBtn).toBeInTheDocument();

    fireEvent.click(collapseBtn);
    expect(localStorage.getItem('pmlytics_sidebar_collapsed')).toBe('true');
  });
});
