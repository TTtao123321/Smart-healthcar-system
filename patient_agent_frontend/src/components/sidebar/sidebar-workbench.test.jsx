import React from 'react'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import HospitalScheduleCard from './HospitalScheduleCard.jsx'
import PatientProfileCard from './PatientProfileCard.jsx'

const appStyles = readFileSync(path.resolve(process.cwd(), 'src/index.css'), 'utf8')

afterEach(() => {
  cleanup()
})

describe('PatientProfileCard', () => {
  it('renders workbench identity markers and visit summaries', () => {
    render(
      <PatientProfileCard
        profile={{
          name: '张三',
          gender: '男',
          age: 36,
          phone: '138****1024',
          idCardMasked: '1234',
          recentVisits: [
            {
              visitId: 'visit-1',
              visitDate: '2026-06-24',
              department: '消化内科',
              doctorName: '李医生',
            },
          ],
        }}
        loading={false}
        loadFailed={false}
      />
    )

    expect(screen.getByText('当前患者')).toBeInTheDocument()
    expect(screen.getByText('已建档')).toBeInTheDocument()
    expect(screen.getByText('消化内科')).toBeInTheDocument()
    expect(screen.getByText('李医生')).toBeInTheDocument()
  })
})

describe('HospitalScheduleCard', () => {
  it('selects the first department with doctors by default and switches on click', () => {
    const onSendChat = vi.fn()

    render(
      <HospitalScheduleCard
        user={{ name: '张三' }}
        onSendChat={onSendChat}
        dateLabel="2026年6月25日 周四"
        loading={false}
        departments={[
          {
            departmentId: 'dept-1',
            departmentName: '全科门诊',
            doctors: [],
          },
          {
            departmentId: 'dept-2',
            departmentName: '心血管内科',
            doctors: [
              {
                doctorId: 'doctor-1',
                doctorName: '王主任',
                title: '主任医师',
                bio: '擅长冠心病与高血压诊疗',
                timeSlots: ['08:00-12:00'],
              },
            ],
          },
          {
            departmentId: 'dept-3',
            departmentName: '神经内科',
            doctors: [
              {
                doctorId: 'doctor-2',
                doctorName: '赵医生',
                title: '副主任医师',
                bio: '擅长头痛与眩晕管理',
                timeSlots: ['14:00-17:30'],
              },
            ],
          },
        ]}
      />
    )

    expect(screen.getByText('王主任')).toBeInTheDocument()
    expect(screen.queryByText('点击具体科室查看排班信息')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: /神经内科/ }))

    expect(screen.getByText('赵医生')).toBeInTheDocument()
  })

  it('closes the confirm modal when switching departments after choosing a doctor', () => {
    render(
      <HospitalScheduleCard
        user={{ name: '张三' }}
        onSendChat={vi.fn()}
        dateLabel="2026年6月25日 周四"
        loading={false}
        departments={[
          {
            departmentId: 'dept-1',
            departmentName: '呼吸与危重症医学科特需联合门诊',
            doctors: [
              {
                doctorId: 'doctor-1',
                doctorName: '王晓晨主任医师',
                title: '主任医师',
                bio: '擅长慢阻肺与哮喘长期管理，提供复杂呼吸系统疾病连续随访。',
                timeSlots: ['08:00-12:00'],
              },
            ],
          },
          {
            departmentId: 'dept-2',
            departmentName: '神经免疫专病门诊',
            doctors: [
              {
                doctorId: 'doctor-2',
                doctorName: '赵明远副主任医师',
                title: '副主任医师',
                bio: '擅长头痛、眩晕与自身免疫性神经疾病管理。',
                timeSlots: ['14:00-17:30'],
              },
            ],
          },
        ]}
      />
    )

    fireEvent.click(screen.getByRole('button', { name: '预约挂号' }))

    expect(screen.getByText('确认挂号信息')).toBeInTheDocument()
    expect(screen.getAllByText('王晓晨主任医师')).toHaveLength(2)

    fireEvent.click(screen.getByRole('tab', { name: /神经免疫专病门诊/ }))

    expect(screen.queryByText('确认挂号信息')).not.toBeInTheDocument()
  })

  it('keeps profile bounded and preserves schedule scrolling rules on short viewports', () => {
    const { container } = render(
      <HospitalScheduleCard
        user={{ name: '张三' }}
        onSendChat={vi.fn()}
        dateLabel="2026年6月25日 周四"
        loading={false}
        departments={Array.from({ length: 12 }, (_, index) => ({
          departmentId: `dept-${index + 1}`,
          departmentName: `测试科室 ${index + 1}`,
          doctors: [
            {
              doctorId: `doctor-${index + 1}`,
              doctorName: `医生 ${index + 1}`,
              title: '主治医师',
              bio: '用于验证排班滚动行为的测试数据',
              timeSlots: ['08:00-12:00'],
            },
          ],
        }))}
      />
    )

    expect(screen.getByRole('tablist', { name: '今日排班科室' })).toBeInTheDocument()
    expect(container.querySelector('.schedule-body-scroll')).not.toBeNull()
    expect(appStyles).toMatch(/\.patient-sidebar\s*\{[^}]*overflow:\s*hidden;/)
    expect(appStyles).toMatch(/\.patient-profile-card\s*\{[^}]*max-height:\s*clamp\(260px,\s*42vh,\s*420px\);/)
    expect(appStyles).toMatch(/\.patient-profile-scroll\s*\{[^}]*overflow-y:\s*auto;/)
    expect(appStyles).toMatch(/\.patient-profile-scroll\s*\{[^}]*min-height:\s*0;/)
    expect(appStyles).toMatch(/\.schedule-card\s*\{[^}]*flex:\s*1;/)
    expect(appStyles).toMatch(/\.schedule-body-scroll\s*\{[^}]*flex:\s*1;/)
    expect(appStyles).toMatch(/\.schedule-body-scroll\s*\{[^}]*overflow-y:\s*auto;/)
    expect(appStyles).not.toMatch(/\.schedule-dept-nav\s*\{[^}]*flex:\s*0 1 240px;/)
    expect(appStyles).toMatch(/\.schedule-current-dept\s*\{[^}]*flex-shrink:\s*0;/)
  })

  it('shows the selected department summary with intro and morning afternoon slot counts', () => {
    render(
      <HospitalScheduleCard
        user={{ name: '张三' }}
        onSendChat={vi.fn()}
        dateLabel="2026年6月25日 周四"
        loading={false}
        departments={[
          {
            departmentId: 'dept-internal',
            departmentName: '内科',
            doctors: [
              {
                doctorId: 'doctor-001',
                doctorName: '张明华',
                title: '主任医师',
                bio: '擅长心血管疾病诊疗，30年临床经验',
                timeSlots: ['08:00-12:00', '14:00-17:00'],
              },
              {
                doctorId: 'doctor-002',
                doctorName: '李芳',
                title: '副主任医师',
                bio: '呼吸系统疾病专家，擅长慢性病管理',
                timeSlots: ['08:30-11:30'],
              },
            ],
          },
        ]}
      />
    )

    expect(screen.getAllByText('内科')).toHaveLength(2)
    expect(
      screen.getByText('擅长心血管疾病诊疗，30年临床经验；呼吸系统疾病专家，擅长慢性病管理')
    ).toBeInTheDocument()
    expect(screen.getByText('上午号源')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('下午号源')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
  })

  it('falls back to default department intro when doctor bios are missing', () => {
    render(
      <HospitalScheduleCard
        user={{ name: '张三' }}
        onSendChat={vi.fn()}
        dateLabel="2026年6月25日 周四"
        loading={false}
        departments={[
          {
            departmentId: 'dept-empty',
            departmentName: '全科门诊',
            doctors: [
              {
                doctorId: 'doctor-003',
                doctorName: '王医生',
                title: '主治医师',
                bio: '',
                timeSlots: [],
              },
            ],
          },
        ]}
      />
    )

    expect(screen.getByText('暂无科室简介')).toBeInTheDocument()
  })

  it('deselects the current department when clicking the selected tab again', () => {
    render(
      <HospitalScheduleCard
        user={{ name: '张三' }}
        onSendChat={vi.fn()}
        dateLabel="2026年6月25日 周四"
        loading={false}
        departments={[
          {
            departmentId: 'dept-1',
            departmentName: '心血管内科',
            doctors: [
              {
                doctorId: 'doctor-1',
                doctorName: '王主任',
                title: '主任医师',
                bio: '擅长冠心病与高血压诊疗',
                timeSlots: ['08:00-12:00'],
              },
            ],
          },
          {
            departmentId: 'dept-2',
            departmentName: '神经内科',
            doctors: [
              {
                doctorId: 'doctor-2',
                doctorName: '赵医生',
                title: '副主任医师',
                bio: '擅长头痛与眩晕管理',
                timeSlots: ['14:00-17:30'],
              },
            ],
          },
        ]}
      />
    )

    const cardioTab = screen.getByRole('tab', { name: /心血管内科/ })
    expect(cardioTab).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByText('王主任')).toBeInTheDocument()

    fireEvent.click(cardioTab)

    expect(cardioTab).toHaveAttribute('aria-selected', 'false')
    expect(screen.queryByText('王主任')).not.toBeInTheDocument()
    expect(screen.getByText('请选择科室查看今日排班')).toBeInTheDocument()
  })

  it('restores the department content after reselecting a tab from empty state', () => {
    render(
      <HospitalScheduleCard
        user={{ name: '张三' }}
        onSendChat={vi.fn()}
        dateLabel="2026年6月25日 周四"
        loading={false}
        departments={[
          {
            departmentId: 'dept-1',
            departmentName: '心血管内科',
            doctors: [
              {
                doctorId: 'doctor-1',
                doctorName: '王主任',
                title: '主任医师',
                bio: '擅长冠心病与高血压诊疗',
                timeSlots: ['08:00-12:00'],
              },
            ],
          },
        ]}
      />
    )

    const cardioTab = screen.getByRole('tab', { name: /心血管内科/ })

    fireEvent.click(cardioTab)
    expect(screen.getByText('请选择科室查看今日排班')).toBeInTheDocument()

    fireEvent.click(cardioTab)

    expect(cardioTab).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByText('王主任')).toBeInTheDocument()
    expect(screen.queryByText('请选择科室查看今日排班')).not.toBeInTheDocument()
  })

  it('closes the confirm modal when deselecting the current department', () => {
    render(
      <HospitalScheduleCard
        user={{ name: '张三' }}
        onSendChat={vi.fn()}
        dateLabel="2026年6月25日 周四"
        loading={false}
        departments={[
          {
            departmentId: 'dept-1',
            departmentName: '心血管内科',
            doctors: [
              {
                doctorId: 'doctor-1',
                doctorName: '王主任',
                title: '主任医师',
                bio: '擅长冠心病与高血压诊疗',
                timeSlots: ['08:00-12:00'],
              },
            ],
          },
        ]}
      />
    )

    fireEvent.click(screen.getByRole('button', { name: '预约挂号' }))
    expect(screen.getByText('确认挂号信息')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: /心血管内科/ }))

    expect(screen.queryByText('确认挂号信息')).not.toBeInTheDocument()
    expect(screen.getByText('请选择科室查看今日排班')).toBeInTheDocument()
  })
})
