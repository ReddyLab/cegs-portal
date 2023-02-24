module.exports = {
    mode: "jit",
    content: ["./cegs_portal/**/*.html", "./cegs_portal/**/*.js", "./node_modules/tw-elements/dist/js/**/*.js"],
    theme: {
        extend: {},
    },
    plugins: [require("tw-elements/dist/plugin")],
};
