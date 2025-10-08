#!/bin/bash
set -e

cd ~/ai-robot-speaker-api

echo "========================================="
echo "  อัปเกรดเป็น WebSocket Real-time"
echo "========================================="
echo ""

# 1. Backup
echo "📦 กำลัง Backup ไฟล์เดิม..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp main.py "main.py.backup.$TIMESTAMP"
if [ -f "static/index.html" ]; then
    cp static/index.html "static/index.html.backup.$TIMESTAMP"
fi
echo "✅ Backup เสร็จแล้ว (main.py.backup.$TIMESTAMP)"
echo ""

# 2. ติดตั้ง dependencies
echo "📦 กำลังติดตั้ง websockets..."
source .venv/bin/activate
pip install -q websockets
echo "✅ ติดตั้ง websockets เสร็จแล้ว"
echo ""

# 3. ดาวน์โหลด main.py ใหม่
echo "📥 กำลังดาวน์โหลด main.py เวอร์ชันใหม่..."
echo "⚠️  คุณต้อง copy main.py จาก artifact และวางที่นี่"
echo ""
echo "📝 หรือใช้คำสั่ง:"
echo "   nano main.py"
echo "   # แล้ว copy โค้ดจาก artifact มาแทนที่ทั้งหมด"
echo ""

# 4. ดาวน์โหลด index.html ใหม่
echo "📥 กำลังดาวน์โหลด static/index.html เวอร์ชันใหม่..."
echo "⚠️  คุณต้อง copy index.html จาก artifact และวางที่ static/"
echo ""
echo "📝 หรือใช้คำสั่ง:"
echo "   nano static/index.html"
echo "   # แล้ว copy โค้ดจาก artifact มาแทนที่ทั้งหมด"
echo ""

# 5. หยุด server เดิม
echo "🛑 หยุด server เดิม..."
pkill -f "python main.py" || true
sleep 3
echo "✅ หยุด server แล้ว"
echo ""

# 6. รีสตาร์ท
echo "🚀 กำลังเริ่ม server ใหม่..."
source .venv/bin/activate
nohup python main.py > server.log 2>&1 &
sleep 3
echo ""

# 7. เช็คสถานะ
echo "========================================="
echo "  ตรวจสอบสถานะ"
echo "========================================="
echo ""

if ps aux | grep -v grep | grep "python main.py" > /dev/null; then
    echo "✅ Server กำลังทำงาน"
    PID=$(ps aux | grep -v grep | grep "python main.py" | awk '{print $2}')
    echo "   PID: $PID"
else
    echo "❌ Server ไม่ทำงาน"
    echo "   ดู logs: tail -f server.log"
    exit 1
fi
echo ""

# 8. ทดสอบ
echo "🧪 ทดสอบการเชื่อมต่อ..."
sleep 2
if curl -s http://localhost:4188/health > /dev/null; then
    echo "✅ API ทำงานปกติ"
else
    echo "⚠️  ไม่สามารถเชื่อมต่อ API"
fi
echo ""

echo "========================================="
echo "  เสร็จสิ้น!"
echo "========================================="
echo ""
echo "🌐 เปิด Web UI:"
echo "   http://192.168.1.59:4188/"
echo "   http://10.147.19.244:4188/ (ZeroTier)"
echo ""
echo "📊 ดู logs:"
echo "   tail -f app.log"
echo "   tail -f server.log"
echo ""
echo "🔄 รีสตาร์ท server:"
echo "   pkill -f 'python main.py' && cd ~/ai-robot-speaker-api && source .venv/bin/activate && nohup python main.py > server.log 2>&1 &"
echo ""
echo "📁 ไฟล์ backup อยู่ที่:"
echo "   main.py.backup.$TIMESTAMP"
echo "   static/index.html.backup.$TIMESTAMP"
echo ""
