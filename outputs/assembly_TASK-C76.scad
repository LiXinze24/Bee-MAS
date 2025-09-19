use <gear.scad>
use <shaft.scad>
use <bearing.scad>

module main_assembly() {
    // 主轴装配
    translate([0, 0, 0])
    rotate([0, 0, 0])
    shaft();
    
    // 齿轮装配到轴上
    translate([0, 0, 20])
    rotate([0, 0, 0])
    gear();
    
    // 前轴承
    translate([0, 0, -10])
    rotate([0, 0, 0])
    bearing();
    
    // 后轴承
    translate([0, 0, 50])
    rotate([0, 0, 0])
    bearing();
}

main_assembly();