// Learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom'

// Mock Next.js router
jest.mock('next/router', () => ({
    useRouter() {
        return {
            route: '/',
            pathname: '',
            query: {},
            asPath: '',
            push: jest.fn(),
            replace: jest.fn(),
        }
    },
}))

// Mock environment variables
process.env = {
    ...process.env,
    NEXT_PUBLIC_API_URL: 'http://localhost:8000',
} 