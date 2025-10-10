/** @type {import('next').NextConfig} */
const nextConfig = {
	async rewrites() {
		return [
			{
				source: "/api/:path*",
				destination: "http://localhost:8000/:path*",
			},
		];
	},
	images: {
		domains: ["github.com", "avatars.githubusercontent.com"],
	},
};

module.exports = nextConfig;
