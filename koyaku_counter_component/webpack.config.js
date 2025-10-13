const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const webpack = require("webpack");

const buildId = new Date().toISOString();

module.exports = {
  entry: "./src/index.tsx",
  resolve: {
    extensions: [".ts", ".tsx", ".js"]
  },
  output: {
    filename: "index.[contenthash].js",
    path: path.resolve(__dirname, "build"),
    library: {
      type: "umd",
      name: "koyaku_counter"
    }
  },
  module: {
    rules: [
      {
        test: /\.m?js$/,
        type: "javascript/auto",
        use: {
          loader: "babel-loader",
          options: {
            cacheDirectory: true
          }
        }
      },
      {
        test: /\.tsx?$/,
        use: [
          {
            loader: "babel-loader"
          },
          {
            loader: "ts-loader"
          }
        ],
        exclude: /node_modules/
      },
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"]
      }
    ]
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: "./public/index.html",
      filename: "index.html",
      scriptLoading: "defer"
    }),
    new webpack.DefinePlugin({
      __BUILD_ID__: JSON.stringify(buildId)
    })
  ],
  devtool: "source-map",
  devServer: {
    static: {
      directory: path.join(__dirname, "public")
    },
    port: 3001,
    hot: true
  }
};