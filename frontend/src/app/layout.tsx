import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
	title: "Watchman Security Platform",
	description:
		"AI-powered autonomous security scanning for GitHub repositories",
};

export default function RootLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	return (
		<html lang="en">
			<body className={`${inter.className} bg-gray-50`}>
				<div className="min-h-screen flex">
					{/* Sidebar */}
					<Sidebar />

					{/* Main Content */}
					<div className="flex-1 flex flex-col ml-64">
						{/* Header */}
						<Header />

						{/* Page Content */}
						<main className="flex-1 p-6">{children}</main>
					</div>
				</div>
			</body>
		</html>
	);
}
