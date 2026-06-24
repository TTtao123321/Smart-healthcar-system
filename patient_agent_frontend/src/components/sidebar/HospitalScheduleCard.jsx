import React, { useEffect, useMemo, useState } from 'react'
import { Calendar, Stethoscope } from 'lucide-react'
import DoctorScheduleList from './DoctorScheduleList.jsx'
import RegisterConfirmModal from './RegisterConfirmModal.jsx'

export default function HospitalScheduleCard({ user, onSendChat, departments, dateLabel, loading }) {
  const [expandedDeptIndex, setExpandedDeptIndex] = useState(null)
  const [confirmDoctor, setConfirmDoctor] = useState(null)
  const firstActiveDeptIndex = useMemo(
    () => departments.findIndex((department) => department.doctors?.length > 0),
    [departments]
  )

  useEffect(() => {
    if (departments.length === 0) {
      setExpandedDeptIndex(null)
      return
    }

    setExpandedDeptIndex(firstActiveDeptIndex >= 0 ? firstActiveDeptIndex : 0)
  }, [departments, firstActiveDeptIndex])

  const activeDepartment = expandedDeptIndex === null ? null : departments[expandedDeptIndex]

  useEffect(() => {
    setConfirmDoctor(null)
  }, [expandedDeptIndex])

  const handleConfirm = () => {
    if (!activeDepartment || !confirmDoctor) return

    onSendChat(`我要预约挂号：${activeDepartment.departmentName} · ${confirmDoctor.doctorName}（${confirmDoctor.title}）`)
    setConfirmDoctor(null)
  }

  return (
    <section className="schedule-card schedule-workbench-card">
      <div className="sidebar-header schedule-workbench-header">
        <div className="schedule-workbench-title">
          <Calendar size={18} className="text-sky" />
          <span>医院排班</span>
        </div>
        <span className="schedule-workbench-caption">按科室切换</span>
      </div>

      <div className="schedule-date">{dateLabel}</div>

      {loading && <div className="schedule-loading">正在加载医院排班...</div>}

      <div className="schedule-dept-nav" role="tablist" aria-label="今日排班科室">
        {departments.map((department, index) => {
          const isActive = expandedDeptIndex === index
          return (
            <button
              key={department.departmentId}
              type="button"
              role="tab"
              aria-selected={isActive}
              className={`schedule-dept-nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setExpandedDeptIndex(index)}
            >
              <span className="schedule-dept-nav-name">{department.departmentName}</span>
              <span className="schedule-dept-nav-meta">{department.doctors.length}位</span>
            </button>
          )
        })}
      </div>

      {activeDepartment ? (
        <div className="schedule-workbench-panel">
          <div className="schedule-current-dept">
            <div className="schedule-current-dept-label">当前科室</div>
            <div className="schedule-current-dept-name">{activeDepartment.departmentName}</div>
          </div>
          <DoctorScheduleList doctors={activeDepartment.doctors} onRegister={setConfirmDoctor} />
        </div>
      ) : departments.length === 0 ? (
        <div className="schedule-placeholder">
          <Stethoscope size={30} className="placeholder-icon" />
          <p className="placeholder-text">当前暂无可展示排班</p>
        </div>
      ) : (
        <div className="schedule-placeholder">
          <Stethoscope size={30} className="placeholder-icon" />
          <p className="placeholder-text">请选择科室查看今日排班</p>
        </div>
      )}

      <RegisterConfirmModal
        user={user}
        departmentName={activeDepartment?.departmentName || ''}
        doctor={confirmDoctor}
        dateLabel={dateLabel}
        onCancel={() => setConfirmDoctor(null)}
        onConfirm={handleConfirm}
      />
    </section>
  )
}
