import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import { Button } from '@/components/primitives/Button';
import { SourceBadge } from '@/components/primitives/SourceBadge';
import { CitationPill } from '@/components/primitives/CitationPill';
import { Badge } from '@/components/primitives/Badge';

describe('UI Primitives', () => {
  it('renders Button with variants and handles click events', () => {
    const handleClick = vi.fn();
    const { getByRole } = render(<Button onClick={handleClick}>Action</Button>);

    const btn = getByRole('button', { name: /action/i });
    expect(btn).toBeInTheDocument();
    btn.click();
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('renders SourceBadge with dedicated provenance colors for Zendesk, PostHog, Jira', () => {
    const { getByText, rerender } = render(<SourceBadge source="zendesk" reference="TICKET-101" />);
    expect(getByText('Zendesk')).toBeInTheDocument();
    expect(getByText('· TICKET-101')).toBeInTheDocument();

    rerender(<SourceBadge source="posthog" reference="funnel_checkout" />);
    expect(getByText('PostHog')).toBeInTheDocument();
    expect(getByText('· funnel_checkout')).toBeInTheDocument();

    rerender(<SourceBadge source="jira" reference="POCKET-404" />);
    expect(getByText('Jira')).toBeInTheDocument();
    expect(getByText('· POCKET-404')).toBeInTheDocument();
  });

  it('renders CitationPill with canonical format and triggers selection handler', () => {
    const handleSelect = vi.fn();
    const { getByRole } = render(<CitationPill evidenceId="EV-001" onSelectCitation={handleSelect} />);

    const pill = getByRole('button', { name: /view evidence record \[ev-001\]/i });
    expect(pill).toBeInTheDocument();
    expect(pill).toHaveTextContent('[EV-001]');

    pill.click();
    expect(handleSelect).toHaveBeenCalledWith('EV-001');
  });

  it('renders Badge with status colors', () => {
    const { getByText } = render(<Badge variant="pass">HIGH CONFIDENCE</Badge>);
    expect(getByText('HIGH CONFIDENCE')).toBeInTheDocument();
  });
});
