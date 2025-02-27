interface PageHeaderProps {
    title: string;
    className?: string;
}

export default function PageHeader({ title, className = "" }: PageHeaderProps) {
    return (
        <div className={`bg-blue-700 text-white p-2 ${className}`}>
            <h2 className="text-lg font-bold">{title}</h2>
        </div>
    );
}
