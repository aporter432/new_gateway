import Logo from './Logo';

interface HeaderProps {
  userName?: string;
  userRole?: string;
  onLogout?: () => void;
}

export default function Header({ userName, userRole, onLogout }: HeaderProps) {
  return (
    <header className="bg-white text-green-500 p-4">
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <Logo className="h-10 w-auto" />
          <h1 className="text-2xl font-bold">Protexis Command</h1>
        </div>

        {userName && (
          <div className="flex items-center space-x-4">
            <div className="flex flex-col items-end">
              <span>Hello, {userName}</span>
              {userRole && (
                <span className="text-xs bg-white px-2 py-0.5 rounded">
                  Role: {userRole}
                </span>
              )}
            </div>
            {onLogout && (
              <button
                onClick={onLogout}
                className="px-4 py-2 bg-white hover:bg-red-700 rounded"
              >
                Log Off
              </button>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
