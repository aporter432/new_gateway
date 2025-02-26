import Logo from './Logo';

export default function Header() {
  return (
    <header className="bg-white shadow">
      <div className="flex justify-between items-center p-4">
        <Logo />
        <nav>{/* Navigation items */}</nav>
      </div>
    </header>
  );
}
