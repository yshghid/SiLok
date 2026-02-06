import { clsx } from 'clsx';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'success' | 'warning' | 'error' | 'gray';
  size?: 'sm' | 'md';
  className?: string;
}

const variantClasses = {
  primary: 'bg-primary-100 text-primary-700',
  success: 'bg-green-100 text-green-700',
  warning: 'bg-yellow-100 text-yellow-700',
  error: 'bg-red-100 text-red-700',
  gray: 'bg-gray-100 text-gray-700',
};

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
};

export function Badge({
  children,
  variant = 'gray',
  size = 'sm',
  className,
}: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center font-medium rounded-full',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
    >
      {children}
    </span>
  );
}

// Platform-specific badges
export function PlatformBadge({ platform }: { platform: string }) {
  const platformConfig: Record<
    string,
    { label: string; variant: BadgeProps['variant'] }
  > = {
    slack: { label: 'Slack', variant: 'primary' },
    notion: { label: 'Notion', variant: 'gray' },
    onedrive: { label: 'OneDrive', variant: 'success' },
    outlook: { label: 'Outlook', variant: 'warning' },
  };

  const config = platformConfig[platform.toLowerCase()] || {
    label: platform,
    variant: 'gray' as const,
  };

  return <Badge variant={config.variant}>{config.label}</Badge>;
}
