const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
	entry: './src/index.tsx', // Entry point for your app
	output: {
		path: path.resolve(__dirname, 'dist'),
		filename: 'bundle.js',
	},
	resolve: {
		extensions: ['.tsx', '.ts', '.js'], // Add extensions for TypeScript and JavaScript
	},
	module: {
		rules: [
			{
				test: /\.tsx?$/, // For handling TypeScript files
				use: 'babel-loader',
				exclude: /node_modules/,
			},
			{
				test: /\.css$/, // For handling CSS files
				use: ['style-loader', 'css-loader'],
			},
			{
				test: /\.(png|jpg|gif|svg)$/, // For handling image files
				use: [
					{
						loader: 'file-loader',
						options: {
							name: '[name].[ext]',
							outputPath: 'assets/',
						},
					},
				],
			},
		],
	},
	devServer: {
		static: {
			directory: path.resolve(__dirname, 'dist'), // Use 'static' instead of 'contentBase'
		},
		hot: true,
		open: true, // Automatically open the browser
		port: 3000, // Specify the port you want to use
	},
	plugins: [
		new HtmlWebpackPlugin({
			template: './public/index.html', // Path to your HTML template
		}),
	],
};
