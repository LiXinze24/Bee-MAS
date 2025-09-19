// 齿轮3D模型 - LLM自动生成
// 参数: 模数=2.0mm, 齿数=20, 压力角=20°, 齿宽=10mm, 孔径=15mm

// 齿轮参数
m = 2.0;           // 模数
z = 20;            // 齿数
alpha = 20;        // 压力角
b = 10;            // 齿宽
d_hole = 15;       // 孔径

// 计算几何参数
d = m * z;         // 分度圆直径
da = d + 2 * m;   // 齿顶圆直径
df = d - 2.5 * m; // 齿根圆直径
p = m * PI;        // 齿距

// 生成齿轮
gear();

module gear() {
    difference() {
        // 齿轮主体
        cylinder(h=b, d=da, $fn=100);
        
        // 中心孔
        cylinder(h=b+1, d=d_hole, $fn=50);
        
        // 齿槽
        for (i = [0:z-1]) {
            rotate([0, 0, i * 360/z])
            translate([d/2, 0, 0])
            tooth_space();
        }
    }
}

module tooth_space() {
    // 精确的齿槽形状
    translate([0, 0, -1])
    linear_extrude(height=b+2)
    polygon([
        [0, 0],
        [m/2, -m/4],
        [m, 0],
        [m/2, m/4]
    ]);
}

// 辅助函数
function PI() = 3.14159;