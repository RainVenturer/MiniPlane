"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import { toast } from "sonner";

export default function SettingsPage() {
  const router = useRouter();
  const { user, setUser, logout } = useAuthStore();
  const [name, setName] = useState(user?.name || "");
  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [saving, setSaving] = useState(false);
  const [changingPw, setChangingPw] = useState(false);

  const saveProfile = async () => {
    setSaving(true);
    try {
      const { data } = await api.put("/auth/me/", { name });
      setUser(data);
      toast.success("个人资料已更新");
    } catch { toast.error("更新失败"); }
    finally { setSaving(false); }
  };

  const changePassword = async () => {
    if (newPw.length < 6) { toast.error("密码至少 6 位"); return; }
    setChangingPw(true);
    try {
      await api.post("/auth/change-password/", { old_password: oldPw, new_password: newPw });
      setOldPw(""); setNewPw("");
      toast.success("密码修改成功");
    } catch { toast.error("密码修改失败，请检查原密码"); }
    finally { setChangingPw(false); }
  };

  return (
    <div className="max-w-lg mx-auto">
      <h2 className="text-2xl font-bold mb-8">个人设置</h2>
      <div className="space-y-6">
        <div className="p-6 bg-surface-1 border border-border rounded-2xl space-y-4">
          <h3 className="text-sm font-semibold">个人资料</h3>
          <Input label="邮箱" value={user?.email || ""} disabled />
          <Input label="姓名" value={name} onChange={(e) => setName(e.target.value)} />
          <Button onClick={saveProfile} disabled={saving || !name}>
            {saving ? "保存中..." : "保存"}
          </Button>
        </div>

        <div className="p-6 bg-surface-1 border border-border rounded-2xl space-y-4">
          <h3 className="text-sm font-semibold">修改密码</h3>
          <Input label="原密码" type="password" value={oldPw} onChange={(e) => setOldPw(e.target.value)} />
          <Input label="新密码" type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)} />
          <Button onClick={changePassword} disabled={changingPw || !oldPw || !newPw}>
            {changingPw ? "修改中..." : "修改密码"}
          </Button>
        </div>
      </div>
    </div>
  );
}
