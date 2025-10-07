const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");

module.exports = {
  entry: "./src/index.tsx",
  resolve: {
    extensions: [".ts", ".tsx", ".js"]
  },
  output: {
    filename: "index.js",
    path: path.resolve(__dirname, "build"),
    library: {
      type: "umd",
      name: "koyaku_counter"
    }
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: "ts-loader",
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