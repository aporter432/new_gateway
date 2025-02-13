import Link from 'next/link';

export default function Home() {
    return (
        <main className="relative min-h-screen w-screen bg-black text-white">
            <div
                className="absolute left-[400px] top-1/2 -translate-y-1/2 w-full max-w-md p-8 bg-white shadow-lg rounded-lg text-center"
            >
                {/* Branding Section */}
                <div className="text-center mb-6">
                    <h1 className="text-3xl font-bold text-black">Protexis Command</h1>
                    <p className="text-sm text-gray-500 mt-2">BECAUSE WE ARENT DICK SUCKERS</p>
                    <p className="text-sm text-gray-500 mt-2">We Know the Work. That's Why We Built the Tech.</p>
                </div>

                {/* Login Form */}
                <form className="w-full space-y-4 flex flex-col items-center">
                    <input
                        type="text"
                        placeholder="Username"
                        className="w-full px-4 py-2 border rounded-lg focus:ring focus:ring-blue-300 focus:outline-none"
                    />
                    <input
                        type="password"
                        placeholder="Password"
                        className="w-full px-4 py-2 border rounded-lg focus:ring focus:ring-blue-300 focus:outline-none"
                    />
                    <button
                        type="submit"
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg transition-all">
                        Sign In
                    </button>
                </form>

                {/* Forgot Password */}
                <div className="mt-4 text-sm">
                    <Link href="#" className="text-blue-600 hover:underline">Forgot Password?</Link>
                </div>

                {/* Footer */}
                <footer className="text-xs text-gray-400 mt-6 text-center">
                    &copy; {new Date().getFullYear()} Protexis Command. All rights reserved.
                </footer>
            </div>
        </main>
    );
}
