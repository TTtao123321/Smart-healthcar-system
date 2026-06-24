import React from 'react'
import { ClipboardList, ShieldCheck, UserCircle } from 'lucide-react'
import RecentVisitsList from './RecentVisitsList.jsx'

export default function PatientProfileCard({ profile, loading, loadFailed }) {
  return (
    <section className="patient-card patient-workbench-card">
      <div className="patient-identity-panel">
        <div className="patient-identity-main">
          <div className="patient-card-title patient-identity-eyebrow">
            <UserCircle size={18} className="text-sky" />
            <span>患者档案</span>
          </div>
          <div className="patient-identity-name">{profile.name || '--'}</div>
          <div className="patient-identity-tags">
            <span className="patient-status-tag">当前患者</span>
            <span className="patient-status-tag patient-status-tag-muted">已建档</span>
          </div>
        </div>
        <span className="patient-card-badge">
          <ShieldCheck size={12} />
          {loadFailed ? '示例数据' : 'HMS 数据'}
        </span>
      </div>

      {(loading || loadFailed) && (
        <div className="patient-card-state-stack">
          {loading && <div className="patient-card-hint">正在加载患者信息...</div>}
          {loadFailed && <div className="patient-card-hint">接口加载失败，当前展示本地示例数据</div>}
        </div>
      )}

      <div className="patient-record-grid">
        <div className="patient-record-row">
          <span className="patient-record-key">性别</span>
          <span className="patient-record-value">{profile.gender || '--'}</span>
        </div>
        <div className="patient-record-row">
          <span className="patient-record-key">年龄</span>
          <span className="patient-record-value">{profile.age ? `${profile.age}岁` : '--'}</span>
        </div>
        <div className="patient-record-row">
          <span className="patient-record-key">手机号</span>
          <span className="patient-record-value">{profile.phone || '--'}</span>
        </div>
        <div className="patient-record-row">
          <span className="patient-record-key">身份证尾号</span>
          <span className="patient-record-value">{profile.idCardMasked || '--'}</span>
        </div>
      </div>

      <div className="patient-visit-section">
        <div className="patient-visit-header">
          <div className="patient-visit-title">
            <ClipboardList size={16} className="text-purple" />
            <span>近期就诊记录</span>
          </div>
          <span className="patient-visit-caption">最近 3 次</span>
        </div>
        <RecentVisitsList visits={profile.recentVisits} />
      </div>
    </section>
  )
}
