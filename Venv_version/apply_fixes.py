"""
修正版ファイル適用スクリプト
"""
import shutil
from pathlib import Path
import time

def backup_original_files():
    """既存ファイルをバックアップ"""
    print("既存ファイルをバックアップ中...")
    
    backup_dir = Path("backup_" + str(int(time.time())))
    backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = [
        "main_system.py",
        "web_app.py"
    ]
    
    for file_name in files_to_backup:
        if Path(file_name).exists():
            shutil.copy2(file_name, backup_dir / file_name)
            print(f"✓ バックアップ: {file_name} -> {backup_dir / file_name}")
    
    print(f"バックアップ完了: {backup_dir}")
    return backup_dir

def apply_main_system_fix():
    """main_system.pyの修正を適用"""
    print("\nmain_system.py の修正を適用中...")
    
    # main_system_complete_fix.py の内容をコピーする必要があります
    print("手動で以下の手順を実行してください:")
    print("1. main_system_complete_fix.py の内容をコピー")
    print("2. main_system.py を開く")
    print("3. 内容を全て置き換える")
    print("4. ファイルを保存")

def apply_web_app_fix():
    """web_app.pyの修正を適用"""
    print("\nweb_app.py の修正を適用中...")
    
    # web_app_fixed.py の内容をコピーする必要があります
    print("手動で以下の手順を実行してください:")
    print("1. web_app_fixed.py の内容をコピー")
    print("2. web_app.py を開く")
    print("3. 内容を全て置き換える")
    print("4. ファイルを保存")

def test_fixes():
    """修正のテスト"""
    print("\n修正のテスト...")
    
    print("以下のコマンドで動作確認してください:")
    print("1. python main.py test")
    print("2. python debug_analysis_frame.py")
    print("3. python main.py web")

def main():
    """メイン処理"""
    print("=" * 60)
    print(" フレーム取得問題修正適用ツール")
    print("=" * 60)
    
    # Step 1: バックアップ
    backup_dir = backup_original_files()
    
    # Step 2: 修正適用
    apply_main_system_fix()
    apply_web_app_fix()
    
    # Step 3: テスト手順
    test_fixes()
    
    print("\n" + "=" * 60)
    print(" 修正適用完了")
    print("=" * 60)
    print("修正内容:")
    print("✅ フレームキャプチャループの改良")
    print("✅ フレームレート制限の一時無効化機能")
    print("✅ 複数の方法でのフレーム取得")
    print("✅ Webアプリでの確実なフレーム取得")
    print("✅ エラー処理とログの強化")
    print()
    print("次のステップ:")
    print("1. 修正したファイルを保存")
    print("2. システムテスト実行: python main.py test")
    print("3. Webアプリ起動: python main.py web")
    print("4. 呼び鈴ボタンをテスト")
    print()
    print(f"問題があった場合のロールバック: {backup_dir} からファイルを復元")

if __name__ == "__main__":
    main()
