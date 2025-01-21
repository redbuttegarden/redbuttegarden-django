const Path = require('path');
const BundleTracker = require("webpack-bundle-tracker");
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const {CleanWebpackPlugin} = require('clean-webpack-plugin');

module.exports = {
    context: __dirname,
    devtool: "source-map",
    mode: 'production',
    entry: './assets/js/index',
    output: {
        path: Path.resolve('./assets/webpack_bundles/'),
        filename: "[name]-[hash].js"
    },
    plugins: [
        new CleanWebpackPlugin(),
        new BundleTracker({relativePath: true, path: __dirname, filename: "webpack-stats.json"}),
        new MiniCssExtractPlugin({
            filename: "[name]-[contenthash].css",
        }),
    ],
    module: {
        rules: [
            {
                test: /\.jsx?$/,
                exclude: /node_modules/,
                use: {
                    loader: "babel-loader",
                },
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
    resolve: {
        extensions: ['', '.js', '.jsx']
    },
};