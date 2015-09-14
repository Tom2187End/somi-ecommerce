var gulp = require("gulp");
var less = require("gulp-less");
var concat = require("gulp-concat");
var uglify = require("gulp-uglify");
var plumber = require("gulp-plumber");
var minifycss = require("gulp-cssnano");
var gutil = require("gulp-util");
var PRODUCTION = gutil.env.production || process.env.NODE_ENV == "production";

gulp.task("less", function() {
    return gulp.src([
        "static_src/less/style.less"
    ])
        .pipe(plumber({}))
        .pipe(less().on("error", function (err) {
            console.log(err.message);
            this.emit("end");
        }))
        .pipe(concat("style.css"))
        .pipe((PRODUCTION ? minifycss() : gutil.noop()))
        .pipe(gulp.dest("static/classic_gray/css/"));
});

gulp.task("less:watch", ["less"], function() {
    gulp.watch(["static_src/less/**/*.less"], ["less"]);
});

gulp.task("js", function() {
    return gulp.src([
        "bower_components/jquery/dist/jquery.js",
        "bower_components/bootstrap/dist/js/bootstrap.js",
        "bower_components/bootstrap-select/js/bootstrap-select.js",
        "static_src/js/custom.js"
    ])
        .pipe(plumber({}))
        .pipe(concat("classic-gray.js"))
        .pipe((PRODUCTION ? uglify() : gutil.noop()))
        .pipe(gulp.dest("static/classic_gray/js/"));
});

gulp.task("js:watch", ["js"], function() {
    gulp.watch(["static_src/js/**/*.js"], ["js"]);
});

gulp.task("default", ["js", "less"]);

gulp.task("watch", ["js:watch", "less:watch"], function() {});
