export default function Logo({ className = "h-10 w-auto" }: { className?: string }) {
  // Use the public folder for assets - all files in public are served at the root path
  return <img src="/images/protexis-logo.png" alt="Protexis Command" className={className} />;
}
