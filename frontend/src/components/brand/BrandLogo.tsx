import Image from 'next/image';
import { cn } from '@/lib/utils';

interface BrandLogoProps {
  className?: string;
  markClassName?: string;
  showName?: boolean;
}

export function BrandLogo({
  className,
  markClassName,
  showName = true,
}: BrandLogoProps) {
  return (
    <span className={cn('inline-flex items-center gap-2.5', className)}>
      <Image
        src="/brand/pmlytics-mark.png"
        alt=""
        width={44}
        height={44}
        priority
        className={cn('h-9 w-9 object-contain', markClassName)}
        aria-hidden="true"
      />
      {showName ? (
        <span
          className="text-[17px] font-extrabold tracking-[-0.03em] text-[#171915]"
          translate="no"
        >
          PMLytics AI
        </span>
      ) : null}
    </span>
  );
}
