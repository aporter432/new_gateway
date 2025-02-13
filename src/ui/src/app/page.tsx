import { MessageForm } from '@/components/forms/MessageForm';

export default function Home() {
    return (
        <main className="container mx-auto px-4 py-8">
            <h1 className="text-2xl font-bold mb-8">Smart Gateway Message Submission</h1>
            <div className="max-w-2xl mx-auto">
                <MessageForm />
            </div>
        </main>
    );
} 