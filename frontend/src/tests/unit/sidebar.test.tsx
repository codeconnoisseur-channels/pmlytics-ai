import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { Sidebar } from '@/components/layout/Sidebar';

const push = vi.fn();
const rename = vi.fn().mockResolvedValue({});
const remove = vi.fn().mockResolvedValue(undefined);

vi.mock('next/navigation', () => ({
  usePathname: () => '/investigations/inv-1',
  useRouter: () => ({ push }),
}));

vi.mock('@/hooks/useInvestigations', () => ({
  useRecentInvestigations: () => ({
    data: [
      {
        investigation_id: 'inv-1',
        user_query: 'Why did transfer completion fall?',
        display_name: null,
        status: 'completed',
      },
    ],
    isLoading: false,
  }),
  useRenameInvestigation: () => ({ mutateAsync: rename, isPending: false }),
  useDeleteInvestigation: () => ({
    mutateAsync: remove,
    isPending: false,
    isError: false,
  }),
}));

describe('Sidebar investigation history actions', () => {
  it('renames an investigation without changing its original question', async () => {
    render(<Sidebar isAuthenticated />);

    fireEvent.click(screen.getByRole('button', { name: /more options for why did transfer completion fall/i }));
    fireEvent.click(screen.getByRole('menuitem', { name: /rename/i }));
    const input = screen.getByLabelText('Investigation name');
    fireEvent.change(input, { target: { value: 'Transfer recovery review' } });
    fireEvent.click(screen.getByRole('button', { name: /save investigation name/i }));

    await waitFor(() => {
      expect(rename).toHaveBeenCalledWith({ id: 'inv-1', displayName: 'Transfer recovery review' });
    });
  });

  it('requires confirmation before deleting an investigation', async () => {
    render(<Sidebar isAuthenticated />);

    fireEvent.click(screen.getByRole('button', { name: /more options for why did transfer completion fall/i }));
    fireEvent.click(screen.getByRole('menuitem', { name: /^delete$/i }));
    expect(screen.getByRole('dialog', { name: /delete this investigation/i })).toBeInTheDocument();
    expect(remove).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: /delete investigation/i }));
    await waitFor(() => expect(remove).toHaveBeenCalledWith('inv-1'));
    expect(push).toHaveBeenCalledWith('/investigations');
  });
});
