const Path = require('path');
const Webpack = require('webpack');
const BundleTracker = require("webpack-bundle-tracker");
const {merge} = require('webpack-merge');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

const common = require('./webpack.common.js');

module.exports = merge(common, {
    target: 'web',
    mode: 'development',
    devtool: 'eval-cheap-source-map',
    output: {
        publicPath: "auto", // necessary for CDNs/S3/blob storages
        filename: "[name]-[contenthash].js",
    },
    devServer: {
        client: {
            logging: 'error',
        },
        hot: true,
    },
    plugins: [
        new Webpack.DefinePlugin({
            'process.env.NODE_ENV': JSON.stringify('development'),
        }),
        new MiniCssExtractPlugin({filename: 'css/app.css',}),
        new BundleTracker({ path: __dirname, filename: "webpack-stats.json" })
    ],
    module: {
        rules: [
            {
                test: /\.html$/i,
                loader: 'html-loader',
            },
            {
                test: /\.js$/,
                include: Path.resolve(__dirname, '../src'),
                loader: 'babel-loader',
            },
            {
                test: /\.s?css$/i,
                use: [
                    MiniCssExtractPlugin.loader,
                    {
                        loader: 'css-loader',
                        options: {
                            import: true,
                            sourceMap: true,
                        },
                    },
                    {
                        loader: 'postcss-loader',
                        options: {
                            postcssOptions: {
                                plugins: () => [
                                    require('autoprefixer')
                                ]
                            }
                        }
                    },
                    'sass-loader',
                ],
            },
        ],
    },
});