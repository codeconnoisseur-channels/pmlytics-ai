import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { InvestigationProgress } from '@/components/workspace/InvestigationProgress';

describe('InvestigationProgress', () => {
  it('starts the verified lifecycle bar at the left edge', () => {
    render(
      <InvestigationProgress
        stage="pending"
        status="connecting"
        elapsedSeconds={0}
        progressStep={0}
        isReconnecting={false}
      />
    );

    const progressbar = screen.getByRole('progressbar', {
      name: /investigation lifecycle progress/i,
    });
    expect(progressbar).toHaveAttribute('aria-valuenow', '0');
    expect(progressbar.firstElementChild).toHaveStyle({ width: '0%' });
    expect(screen.queryByText(/reconnecting securely/i)).not.toBeInTheDocument();
  });

  it('advances from backend lifecycle stages and explains real reconnection', () => {
    render(
      <InvestigationProgress
        stage="reviewing"
        status="connecting"
        activeAgent="critic"
        elapsedSeconds={68}
        progressStep={4}
        isReconnecting
      />
    );

    const progressbar = screen.getByRole('progressbar', {
      name: /investigation lifecycle progress/i,
    });
    expect(progressbar).toHaveAttribute('aria-valuenow', '4');
    expect(progressbar).toHaveAttribute('aria-valuetext', 'Checking the recommendation. Step 4 of 6.');
    expect(screen.getByText(/reconnecting securely/i)).toBeInTheDocument();
  });

  it('shows a full bar and completion state before the report is revealed', () => {
    render(
      <InvestigationProgress
        stage="completed"
        status="completed"
        elapsedSeconds={117}
        progressStep={6}
      />
    );

    expect(screen.getByText('Analysis complete')).toBeInTheDocument();
    expect(screen.getByText('Your decision brief is ready')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '6');
    expect(screen.getByRole('progressbar').firstElementChild).toHaveStyle({ width: '100%' });
  });
});
