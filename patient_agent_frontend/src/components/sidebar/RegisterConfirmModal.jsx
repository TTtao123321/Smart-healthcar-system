import React from 'react'
import { CircleAlert, X } from 'lucide-react'

export default function RegisterConfirmModal({
  user,
  departmentName,
  doctor,
  dateLabel,
  onCancel,
  onConfirm,
}) {
  if (!doctor) return null

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-card modal-workbench-card" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header modal-workbench-header">
          <span className="modal-title">确认挂号信息</span>
          <button onClick={onCancel} className="modal-close">
            <X size={18} />
          </button>
        </div>

        <div className="modal-body modal-workbench-body">
          <div className="modal-doctor">
            <div className="modal-avatar">{doctor.doctorName[0]}</div>
            <div className="modal-doctor-info">
              <div className="modal-doctor-name">{doctor.doctorName}</div>
              <div className="modal-doctor-title">{doctor.title}</div>
              <div className="modal-dept">{departmentName}</div>
            </div>
          </div>

          <div className="modal-details">
            <div className="modal-row">
              <span className="modal-label">就诊日期</span>
              <span className="modal-value">{dateLabel}</span>
            </div>
            <div className="modal-row">
              <span className="modal-label">出诊时段</span>
              <span className="modal-value">{doctor.timeSlots.join(' / ')}</span>
            </div>
            <div className="modal-row">
              <span className="modal-label">就诊科室</span>
              <span className="modal-value">{departmentName}</span>
            </div>
            <div className="modal-row">
              <span className="modal-label">就诊患者</span>
              <span className="modal-value">{user.name}</span>
            </div>
          </div>

          <p className="modal-note">
            <CircleAlert size={14} />
            确认后将通过 AI 助手提交挂号申请
          </p>
        </div>

        <div className="modal-footer">
          <button onClick={onCancel} className="modal-btn modal-btn-cancel">取消</button>
          <button onClick={onConfirm} className="modal-btn modal-btn-confirm">确认挂号</button>
        </div>
      </div>
    </div>
  )
}
